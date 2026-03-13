import cv2
import numpy as np

print("--- 키 코드 테스터 ---")
print("검은색 창을 마우스로 클릭한 후, 키를 누르세요.")
print("찾으려는 키 (왼쪽/오른쪽 화살표)를 누르고 터미널에 나오는 숫자를 확인하세요.")
print("확인이 끝나면 'q' 키를 눌러 종료합니다.")

# 300x300 크기의 검은색 이미지 생성
img = np.zeros((300, 500, 3), dtype=np.uint8)
window_name = "Key Code Tester (Press 'q' to quit)"

cv2.putText(img, "Click this window", (100, 130), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
cv2.putText(img, "Check your terminal for key codes", (50, 180), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1)

while True:
    cv2.imshow(window_name, img)
    
    # 키 입력을 무한정 대기 (Ex 버전)
    key = cv2.waitKeyEx(0)

    if key == -1:
        continue

    print(f"방금 누른 키의 코드는: {key}")

    if key == ord('q'):
        print("테스트를 종료합니다.")
        break

cv2.destroyAllWindows()