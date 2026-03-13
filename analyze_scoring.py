import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm # (v3) 한글 폰트 매니저
import numpy as np
import os
import glob 
import sys  

# --- (v3) 1. 폰트 및 플롯 설정 ---
FONT_PATH = "NanumGothicBold.ttf" 

# 폰트가 있는지 확인하고 matplotlib에 등록
if os.path.exists(FONT_PATH):
    # 폰트 매니저에 폰트 추가
    fm.fontManager.addfont(FONT_PATH)
    # matplotlib의 기본 폰트를 'NanumGothicBold'로 설정
    plt.rc('font', family=fm.FontProperties(fname=FONT_PATH).get_name())
    print(f"--- 폰트 로드 성공: {FONT_PATH} ---")
else:
    print(f"--- [경고] 폰트 파일 '{FONT_PATH}'를 찾을 수 없습니다. ---")
    print("--- 한글이 깨지거나 오류가 발생할 수 있습니다. ---")

# 한글 사용 시 마이너스 부호 깨짐 방지
plt.rcParams['axes.unicode_minus'] = False 

# 스코어링 툴과 동일한 색상
BEHAVIOR_COLORS = {
    'rearing': '#00FF00',  # 초록
    'grooming': '#FFFF00', # 노랑
    'climbing': '#FFaa00'  # 주황
}
# -----------------------------

# --- 2. 대화형 파일 선택 (v2와 동일) ---
print("\n--- Ethogram 분석기 v3 ---")
user_name = input("분석할 실험자의 이름을 입력하세요: ")

if not user_name:
    print("이름이 입력되지 않았습니다. 프로그램을 종료합니다.")
    sys.exit()

search_pattern = f"scoring_log_*{user_name}*.csv"
found_files = glob.glob(search_pattern)
FILE_NAME = None 

if len(found_files) == 0:
    print(f"\n[오류] '{user_name}'님의 스코어링 로그 파일 ('{search_pattern}')을 찾을 수 없습니다.")
    sys.exit()
elif len(found_files) == 1:
    FILE_NAME = found_files[0]
    print(f"\n파일을 1개 찾았습니다: {FILE_NAME}")
    confirm = input("이 파일로 분석을 진행할까요? (y/n): ").lower()
    if confirm != 'y':
        print("분석을 취소합니다.")
        sys.exit()
else:
    print(f"\n'{user_name}'님의 파일을 {len(found_files)}개 찾았습니다. 분석할 파일을 선택하세요:")
    for i, file in enumerate(found_files):
        print(f"  [{i+1}] {file}")
    try:
        choice_str = input(f"번호를 입력하세요 (1~{len(found_files)}): ")
        choice_idx = int(choice_str) - 1
        if 0 <= choice_idx < len(found_files):
            FILE_NAME = found_files[choice_idx]
            print(f"선택된 파일: {FILE_NAME}")
        else:
            print("잘못된 번호입니다. 분석을 취소합니다.")
            sys.exit()
    except ValueError:
        print("숫자를 입력해야 합니다. 분석을 취소합니다.")
        sys.exit()

print("----------------------------------------")

# --- 3. 데이터 로드 (v2와 동일) ---
try:
    df = pd.read_csv(FILE_NAME, comment='#', encoding='utf-8-sig')
    print(f"--- 1. 파일 로드 성공: {FILE_NAME} ---")
except Exception as e:
    print(f"파일 로드 중 오류 발생: {e}")
    sys.exit()
if df.empty:
    print("\n파일에 분석할 데이터가 없습니다.")
    sys.exit()

# --- 4. 'Bout' (행동 구간) 데이터프레임 생성 (v2와 동일) ---
try:
    starts_df = df[df['Event'] == 'START'][['Behavior', 'Time (sec)']].rename(columns={'Time (sec)': 'start_time'})
    ends_df = df[df['Event'] == 'END'][['Behavior', 'Time (sec)']].rename(columns={'Time (sec)': 'end_time'})
    starts_df['bout_id'] = starts_df.groupby('Behavior').cumcount()
    ends_df['bout_id'] = ends_df.groupby('Behavior').cumcount()
    bouts_df = pd.merge(starts_df, ends_df, on=['Behavior', 'bout_id'])
    bouts_df['duration'] = bouts_df['end_time'] - bouts_df['start_time']
    print("\n--- 2. 행동 구간 (Bouts) 분석 완료 ---")
except Exception as e:
    print(f"\n--- 2. 행동 구간 분석 중 오류 (START/END 쌍 불일치?) ---")
    sys.exit()
if bouts_df.empty:
    print("\n분석할 행동 구간이 없습니다. (START/END 쌍이 없음)")
    sys.exit()

# --- 5. (v3) 통계 분석 (Maximum 추가) ---
print("\n--- 3. 행동별 요약 통계 ---")

# A. 총 시간(sum), 빈도(count), 평균 시간(mean), 최대 시간(max)
analysis = bouts_df.groupby('Behavior')['duration'].agg(['sum', 'count', 'mean', 'max'])
analysis.columns = [
    'Total Duration (s)', 
    'Frequency (n)', 
    'Mean Duration (s)', 
    'Maximum Duration (s)' # (v3) 최대 시간 추가
]
print(analysis)

# B. 첫 행동까지의 잠복기 (Latency)
latency = bouts_df.groupby('Behavior')['start_time'].min().reset_index()
latency.columns = ['Behavior', 'Latency to First Bout (s)']
print("\n--- 3b. 첫 행동 잠복기 ---")
print(latency)


# --- 6. (v3) Ethogram 타임라인 플롯 생성 (v2와 동일) ---
print("\n--- 4. Ethogram 플롯 생성 중 ---")

behaviors_list = sorted(bouts_df['Behavior'].unique())
y_ticks = [(i + 1) * 10 for i in range(len(behaviors_list))]
y_labels = [b.title() for b in behaviors_list]

plt.figure(figsize=(15, 5)) 
ax = plt.gca()

for i, behavior in enumerate(behaviors_list):
    bouts = bouts_df[bouts_df['Behavior'] == behavior]
    xranges = list(zip(bouts['start_time'], bouts['duration']))
    yrange = (y_ticks[i] - 2, 4) 
    color = BEHAVIOR_COLORS.get(behavior, 'gray')
    ax.broken_barh(xranges, yrange, facecolors=color, label=behavior.title())

ax.set_yticks(y_ticks)
ax.set_yticklabels(y_labels) # 한글 폰트 적용됨
ax.set_xlabel('시간 (Time, seconds)') # (v3) 한글 병기
ax.set_ylabel('행동 (Behaviors)') # (v3) 한글 병기
ax.set_title('Ethogram 타임라인 플롯 (Timeline Plot)') # (v3) 한글 병기

# 비디오 총 길이 (CSV 메타데이터에서 읽어오기)
try:
    with open(FILE_NAME, 'r', encoding='utf-8-sig') as f:
        lines = f.readlines()
        total_frames_line = [line for line in lines if '총 프레임' in line][0]
        fps_line = [line for line in lines if 'FPS' in line][0]
        
        total_frames = int(total_frames_line.split(':')[1].strip())
        fps = float(fps_line.split(':')[1].strip())
        total_duration = total_frames / fps
        
        ax.set_xlim(0, total_duration)
        print(f"비디오 총 길이 ({total_duration:.2f}s)를 X축에 적용했습니다.")
except Exception as e:
    print(f"비디오 총 길이 읽기 실패 (플롯 X축 자동 설정): {e}")

plt.grid(axis='x', linestyle='--', alpha=0.7)
plt.tight_layout()

base_file_name = os.path.splitext(os.path.basename(FILE_NAME))[0]
plot_filename = f'plot_{base_file_name}.png'
plt.savefig(plot_filename)
print(f"Ethogram 플롯이 '{plot_filename}' 파일로 저장되었습니다.")


# --- 7. (v3) 요약 바 플롯 (Bar Plots) 생성 ---
print("\n--- 5. 요약 바 플롯 생성 중 ---")

# 플롯을 그리기 위해 데이터 정렬
behaviors_index = analysis.index
colors = [BEHAVIOR_COLORS.get(b, 'gray') for b in behaviors_index]

# Latency 데이터프레임도 동일한 순서로 정렬
latency_df = latency.set_index('Behavior').reindex(behaviors_index)

# 2x2 서브플롯 생성
fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.suptitle(f'행동 분석 요약: {os.path.basename(FILE_NAME)}', fontsize=18, y=1.03)

# A. 총 행동 시간 (Total Duration)
axes[0, 0].bar(behaviors_index, analysis['Total Duration (s)'], color=colors)
axes[0, 0].set_title('총 행동 시간 (Total Duration)', fontsize=14)
axes[0, 0].set_ylabel('시간 (Time, s)')

# B. 평균 행동 시간 (Mean Duration)
axes[0, 1].bar(behaviors_index, analysis['Mean Duration (s)'], color=colors)
axes[0, 1].set_title('평균 행동 시간 (Mean Duration)', fontsize=14)
axes[0, 1].set_ylabel('시간 (Time, s)')

# C. 최대 행동 시간 (Maximum Duration)
axes[1, 0].bar(behaviors_index, analysis['Maximum Duration (s)'], color=colors)
axes[1, 0].set_title('최대 행동 시간 (Maximum Duration)', fontsize=14)
axes[1, 0].set_ylabel('시간 (Time, s)')

# D. 첫 행동 잠복기 (Latency)
axes[1, 1].bar(behaviors_index, latency_df['Latency to First Bout (s)'], color=colors)
axes[1, 1].set_title('첫 행동 잠복기 (Latency to First Bout)', fontsize=14)
axes[1, 1].set_ylabel('시간 (Time, s)')

# 레이아웃 정리 및 저장
plt.tight_layout(rect=[0, 0.03, 1, 0.95]) # suptitle과 겹치지 않게
bar_plot_filename = f'bar_plots_{base_file_name}.png'
plt.savefig(bar_plot_filename)
print(f"바 플롯이 '{bar_plot_filename}' 파일로 저장되었습니다.")