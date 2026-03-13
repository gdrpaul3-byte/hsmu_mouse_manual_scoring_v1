import cv2
import csv
import sys
import os
import numpy as np
import time 

from PIL import ImageFont, ImageDraw, Image

# --- 폰트 설정 ---
FONT_PATH = "NanumGothicBold.ttf" 
if not os.path.exists(FONT_PATH):
    print(f"오류: 폰트 파일 '{FONT_PATH}'를 찾을 수 없습니다.")
    print("스크립트와 같은 폴더에 'NanumGothicBold.ttf' 파일을 넣어주세요.")
    sys.exit()

font_small = ImageFont.truetype(FONT_PATH, 16) 
font_medium = ImageFont.truetype(FONT_PATH, 19) 
font_large = ImageFont.truetype(FONT_PATH, 22) 

def draw_text_pil(img_np, text, pos, font, color):
    img_pil = Image.fromarray(cv2.cvtColor(img_np, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(img_pil)
    draw.text(pos, text, font=font, fill=(color[2], color[1], color[0]))
    return cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)


# --- 1. 사용자 정보 입력 ---
print("OpenCV 스코어링 프로그램을 시작합니다.")
print("비디오를 로드하기 전에 스코어링 정보를 입력하세요.")
user_name = input("  실험자 이름: ")
user_id = input("  실험자 학번/ID: ")
print(f"\n환영합니다, {user_name}님. 비디오를 로드합니다...")
print("----------------------------------------")

# --- 설정 ---
VIDEO_FILE = "mouse_video.mp4"
OUTPUT_FILE = f"scoring_log_{user_id}_{user_name}.csv" 

BEHAVIOR_LIST = ['rearing', 'grooming', 'climbing']
# (v12) 위/아래 키 순환을 위해 None(선택 안 함) 추가
BEHAVIOR_LIST_CYCLE = BEHAVIOR_LIST + [None] 

BEHAVIOR_COLORS = {
    'rearing': (0, 255, 0),
    'grooming': (0, 255, 255),
    'climbing': (255, 170, 0)
}
COLOR_OFF = (80, 80, 80)
COLOR_PADDING = (30, 30, 30)
COLOR_FIXED = (100, 100, 100)
COLOR_PENDING = (255, 0, 255)

# --- (v12) "단일 채널 선택" 로직 변수 ---
selected_index = len(BEHAVIOR_LIST_CYCLE) - 1 # 맨 마지막 [None]에서 시작
selected_behavior = BEHAVIOR_LIST_CYCLE[selected_index] # None
current_mode_on = False 
# ------------------------------------

# 비디오 파일 열기
cap = cv2.VideoCapture(VIDEO_FILE)
if not cap.isOpened():
    print(f"오류: 비디오 파일({VIDEO_FILE})을 열 수 없습니다.")
    sys.exit()

# 비디오 정보
total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
fps = cap.get(cv2.CAP_PROP_FPS)
if fps == 0:
    print("경고: FPS 정보를 읽을 수 없습니다. 기본값 (30)으로 설정합니다.")
    fps = 30

target_frame_time_ms = 1000 / fps

behavior_states = {b: np.zeros(total_frames, dtype=bool) for b in BEHAVIOR_LIST}

current_frame_num = 0
is_paused = True 

window_name = "Advanced Scoring Tool"
cv2.namedWindow(window_name, cv2.WINDOW_NORMAL) 

cap.set(cv2.CAP_PROP_POS_FRAMES, current_frame_num)
ret, frame = cap.read()
if not ret:
    print("오류: 비디오에서 프레임을 읽을 수 없습니다.")
    sys.exit()

# 10초 윈도우 프레임 수 계산 (홀수일 경우 +1 보정)
WINDOW_DURATION_SEC = 10
window_total_frames = int(fps * WINDOW_DURATION_SEC)
if window_total_frames % 2 != 0:
    window_total_frames += 1
window_half_frames = window_total_frames // 2

print("--- 키보드 안내 ---")
print(f" 비디오: {VIDEO_FILE} (총 {total_frames} 프레임, {fps:.2f} fps)")
print(f" 실험자: {user_name} ({user_id})")
print(" ------------------")
print(" ↑ / ↓   : 수정할 행동 채널 [선택] (R/G/C/None)")
print(" ENTER   : [선택]된 채널의 'Mode' (ON/OFF) 토글")
print(" ------------------")
print(" SPACE   : 재생 / 일시정지")
print(" → (오른쪽): (일시정지 시) 1 프레임 앞으로 (페인팅 O)")
print(" ← (왼쪽)  : (일시정지 시) 1 프레임 뒤로 (읽기 전용)")
print(" q       : 종료 및 로그 저장")
print(" ------------------")


while True:
    t_start = time.time()
    
    # 1. 프레임 읽기 (v11 로직)
    if is_paused: 
        cap.set(cv2.CAP_PROP_POS_FRAMES, current_frame_num)
        ret, frame = cap.read()
    else:
        # (v11) 재생 중일 땐, "페인팅"을 먼저 수행
        if selected_behavior is not None:
            behavior_states[selected_behavior][current_frame_num] = current_mode_on
            
        ret, frame = cap.read()
        if ret:
            current_frame_num = int(cap.get(cv2.CAP_PROP_POS_FRAMES)) - 1
    
    if not ret:
        print("비디오의 끝에 도달했습니다.")
        is_paused = True
        current_frame_num = total_frames - 1
        cap.set(cv2.CAP_PROP_POS_FRAMES, current_frame_num)
        ret, frame = cap.read()
        if not ret:
            break 
    
    # --- 3. 시각화 패널 생성 ---
    h, w, _ = frame.shape
    sidebar_width = 350 
    sidebar = np.full((h, sidebar_width, 3), (20, 20, 20), dtype=np.uint8)

    # --- 4. 시간 정보 및 기타 텍스트 준비 ---
    current_time_sec = current_frame_num / fps
    total_time_sec = total_frames / fps
    
    def format_time(seconds):
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        ms = int((seconds - int(seconds)) * 1000)
        return f"{mins:02}:{secs:02}.{ms:03}"

    time_str = f"시간: {format_time(current_time_sec)} / {format_time(total_time_sec)}"
    frame_str = f"프레임: {current_frame_num} / {total_frames}"
    pause_str = "일시정지" if is_paused else "재생 중"
    
    # --- 5. 사이드바에 정보 그리기 ---
    y_offset = 30
    sidebar = draw_text_pil(sidebar, "Made by Sunwhi Kim", (10, h - 25), font_small, (150, 150, 150))
    sidebar = draw_text_pil(sidebar, f"실험자: {user_name} ({user_id})", (10, y_offset), font_medium, (255, 255, 255))
    y_offset += 40
    sidebar = draw_text_pil(sidebar, pause_str, (10, y_offset), font_medium, (0, 0, 255) if is_paused else (0, 255, 0))
    y_offset += 30
    sidebar = draw_text_pil(sidebar, frame_str, (10, y_offset), font_medium, (255, 255, 255))
    y_offset += 30
    sidebar = draw_text_pil(sidebar, time_str, (10, y_offset), font_medium, (255, 255, 255))
    y_offset += 50
    sidebar = draw_text_pil(sidebar, f"타임라인 (중앙 T +/- {WINDOW_DURATION_SEC/2}초)", (10, y_offset), font_small, (200, 200, 200))
    y_offset += 25

    # --- 6. (v12) 행동 시각화 바 그리기 ---
    bar_width = sidebar_width - 20
    bar_height = 20

    for i, behavior in enumerate(BEHAVIOR_LIST):
        
        is_selected = (behavior == selected_behavior)
        
        # A. 상태 텍스트 (e.g., "(r) Rearing [SELECTED]")
        select_str = "[SELECTED]" if is_selected else ""
        behavior_label = f"{behavior.title()} {select_str}"
        
        # B. 텍스트 색상
        if is_selected:
            color = BEHAVIOR_COLORS[behavior] if current_mode_on else COLOR_PENDING # (Selected-ON = Color, Selected-OFF = Pink)
        else:
            color = COLOR_FIXED # (Fixed = Gray)
            
        sidebar = draw_text_pil(sidebar, behavior_label, (10, y_offset), font_large, color)
        
        # C. 모드 텍스트 (선택된 채널에만 표시)
        if is_selected:
            mode_str = "Mode: ON" if current_mode_on else "Mode: OFF"
            y_offset_state = y_offset + font_large.getbbox(behavior_label)[3] + 2
            sidebar = draw_text_pil(sidebar, f"    (ENTER) {mode_str}", (10, y_offset_state), font_medium, color)
            bar_y = y_offset_state + font_medium.getbbox(f"    (ENTER) {mode_str}")[3] + 5 
        else:
            bar_y = y_offset + font_large.getbbox(behavior_label)[3] + 5 
        
        # --- 10초 윈도우 데이터 슬라이스 (v5와 동일) ---
        window_data = np.full(window_total_frames, False, dtype=bool)
        data_start = current_frame_num - window_half_frames
        data_end = current_frame_num + window_half_frames
        slice_start = max(0, data_start)
        slice_end = min(total_frames, data_end)
        actual_data_slice = behavior_states[behavior][slice_start:slice_end]
        window_start_index = max(0, -data_start)
        window_end_index = window_total_frames - max(0, data_end - total_frames)
        if len(actual_data_slice) > 0 and (window_end_index > window_start_index):
             window_data[window_start_index:window_end_index] = actual_data_slice
        
        # --- 바(Bar) 그리기 (v5와 동일) ---
        indices = np.linspace(0, bar_width, window_total_frames, dtype=int)
        unique_indices, starts = np.unique(indices, return_index=True)
        x_start = 10
        for k in range(len(unique_indices) - 1):
            idx_in_states = starts[k]
            x_end = 10 + unique_indices[k+1]
            is_padded = (idx_in_states < window_start_index) or (idx_in_states >= window_end_index)
            if is_padded:
                bar_color = COLOR_PADDING
            else:
                is_active = window_data[idx_in_states]
                bar_color = BEHAVIOR_COLORS[behavior] if is_active else COLOR_OFF
            cv2.rectangle(sidebar, (x_start, bar_y), (x_end, bar_y + bar_height), bar_color, -1)
            x_start = x_end
        is_padded = (window_total_frames - 1 < window_start_index) or (window_total_frames - 1 >= window_end_index)
        if is_padded:
            bar_color = COLOR_PADDING
        else:
            is_active = window_data[-1]
            bar_color = BEHAVIOR_COLORS[behavior] if is_active else COLOR_OFF
        cv2.rectangle(sidebar, (x_start, bar_y), (10 + bar_width, bar_y + bar_height), bar_color, -1)
        
        # --- 중앙에 빨간 선 그리기 (v5와 동일) ---
        bar_center_x = 10 + (bar_width // 2)
        cv2.line(sidebar, (bar_center_x, bar_y - 2), (bar_center_x, bar_y + bar_height + 2), (0, 0, 255), 1)
        
        y_offset = bar_y + bar_height + 20 

    # 7. 최종 화면 표시 (v9 수정: waitKey 전에 표시)
    display_image = np.hstack((frame, sidebar))
    cv2.imshow(window_name, display_image)

    # 8. 재생 속도 보정 및 키 입력
    if is_paused:
        wait_time_ms = 0 
    else:
        t_end = time.time()
        processing_time_ms = (t_end - t_start) * 1000
        wait_time_ms = int(target_frame_time_ms - processing_time_ms)
        if wait_time_ms <= 0:
            wait_time_ms = 1 
            
    key = cv2.waitKeyEx(wait_time_ms)

    # 9. 키 처리 로직
    if key == -1:
        continue # 재생 중 키 입력 없음

    if key == ord('q'):
        break
    
    elif key == ord(' '):
        is_paused = not is_paused
    
    # --- (v12) 키 처리 로직 ---
    elif key == 38: # 위 화살표 (Up)
        selected_index = (selected_index - 1) % len(BEHAVIOR_LIST_CYCLE)
        selected_behavior = BEHAVIOR_LIST_CYCLE[selected_index]
        if selected_behavior is not None:
            current_mode_on = behavior_states[selected_behavior][current_frame_num]
            print(f"채널 [SELECTED] -> {selected_behavior.title()} (Mode: {'ON' if current_mode_on else 'OFF'})")
        else:
            current_mode_on = False
            print(f"채널 [SELECTED] -> None (페인팅 중지)")

    elif key == 40: # 아래 화살표 (Down)
        selected_index = (selected_index + 1) % len(BEHAVIOR_LIST_CYCLE)
        selected_behavior = BEHAVIOR_LIST_CYCLE[selected_index]
        if selected_behavior is not None:
            current_mode_on = behavior_states[selected_behavior][current_frame_num]
            print(f"채널 [SELECTED] -> {selected_behavior.title()} (Mode: {'ON' if current_mode_on else 'OFF'})")
        else:
            current_mode_on = False
            print(f"채널 [SELECTED] -> None (페인팅 중지)")
            
    elif key == 13 or key == 10: # ENTER 키
        if selected_behavior is not None:
            current_mode_on = not current_mode_on
            mode_str = "ON" if current_mode_on else "OFF"
            print(f"[{selected_behavior.title()}] 'Mode' 변경 -> {mode_str}")
        else:
            print(f"[!] 'Mode' 변경 실패. (먼저 '↑/↓' 키로 채널을 선택하세요)")
            
    elif is_paused:
        # --- (v11) 읽기 전용/쓰기 분리 로직 ---
        new_frame_num = current_frame_num
        
        if key == 37: # 왼쪽 화살표 (읽기 전용)
            new_frame_num = current_frame_num - 1
            
        elif key == 39: # 오른쪽 화살표 (페인팅 O)
            new_frame_num = current_frame_num + 1
            
            # (v11) 오른쪽으로 갈 때만 페인팅
            if selected_behavior is not None:
                if 0 <= new_frame_num < total_frames:
                    behavior_states[selected_behavior][new_frame_num] = current_mode_on
        
        # 프레임 업데이트
        if new_frame_num != current_frame_num:
            if new_frame_num < 0:
                current_frame_num = 0
            elif new_frame_num >= total_frames:
                current_frame_num = total_frames - 1
            else:
                current_frame_num = new_frame_num
                
            cap.set(cv2.CAP_PROP_POS_FRAMES, current_frame_num)

# --- 10. 종료 및 저장 (v11과 동일, utf-8-sig) ---
cap.release()
cv2.destroyAllWindows()

print("\n분석이 종료되었습니다. 로그 데이터를 CSV 파일로 변환합니다...")

final_log = []
final_log.append(["Frame", "Time (sec)", "Event", "Behavior"])

for behavior in BEHAVIOR_LIST:
    states = behavior_states[behavior].astype(int) 
    diffs = np.diff(states, prepend=0, append=0)
    
    start_frames = np.where(diffs == 1)[0]
    end_frames = np.where(diffs == -1)[0]

    for f in start_frames:
        if f < total_frames:
            time_sec = f / fps
            final_log.append([f, f"{time_sec:.3f}", "START", behavior])

    for f in end_frames:
        if f < total_frames:
            time_sec = f / fps
            final_log.append([f, f"{time_sec:.3f}", "END", behavior])

header = final_log[0]
data = sorted(final_log[1:], key=lambda x: x[0])
final_log = [header] + data

try:
    with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        
        writer.writerow([f"# 실험자 이름: {user_name}"])
        writer.writerow([f"# 실험자 학번/ID: {user_id}"])
        writer.writerow([f"# 비디오 파일: {VIDEO_FILE}"])
        writer.writerow([f"# 총 프레임: {total_frames}"])
        writer.writerow([f"# FPS: {fps:.3f}"])
        writer.writerow(["# ------------------"])
        
        writer.writerows(final_log)
        
    print(f"성공! '{OUTPUT_FILE}' 파일에 저장되었습니다.")

except PermissionError:
    print(f"\n오류: '{OUTPUT_FILE}' 파일에 쓸 권한이 없습니다. (Excel 등에서 열려있는지 확인하세요)")
except Exception as e:
    print(f"오류: 파일 저장에 실패했습니다. ({e})")