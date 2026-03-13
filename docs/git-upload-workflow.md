# Git Upload Workflow
> 프로젝트 폴더를 정리하고 GitHub에 업로드하는 반복 가능한 워크플로우

---

## 1단계: 폴더 구조 파악
폴더 안의 파일들을 성격별로 분류합니다.
- **코드** (`.py`, `.js` 등)
- **에셋/리소스** (폰트, 이미지 등)
- **데이터/결과물** (CSV, PNG, 보고서 등)
- **영상/대용량 바이너리** (`.mp4` 등)

---

## 2단계: 폴더 정리
```
프로젝트/
├── 코드 파일들          ← 루트에 (또는 src/)
├── assets/             ← 폰트, 이미지 등
├── sample_data/        ← 익명화된 예시 데이터 1건
├── private_data/       ← 실제 데이터 (.gitignore 처리)
└── docs/               ← 설정 메모, 참고 문서
```
- 버전 번호 제거: `tool_v12.py` → `tool.py`
- 개인정보 포함 파일은 별도 폴더로 분리

---

## 3단계: GitHub용 파일 3종 생성

### `.gitignore` — 올리면 안 되는 것들
```gitignore
*.mp4                    # 대용량 영상
private_data/            # 개인정보
output_log_*.csv         # 자동 생성 결과물
!sample_data/            # 단, 샘플 폴더는 예외
__pycache__/
*.pyc
.DS_Store
Thumbs.db
venv/
```

### `requirements.txt` — 패키지 목록
```
opencv-python
numpy
Pillow
pandas
matplotlib
```

### `README.md` — 프로젝트 설명
구성, 설치 방법, 사용법, 주의사항 포함

---

## 4단계: 프로그램 실행 화면 캡처 (선택)
GUI 없이 OpenCV 렌더링 결과를 PNG로 저장:
```python
# cv2.imshow() 대신 cv2.imwrite() 사용
cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
ret, frame = cap.read()
# ... UI 오버레이 렌더링 ...
cv2.imwrite("screenshot.png", display_image)
```

---

## 5단계: Git 업로드
```bash
git init
git add .
git commit -m "Initial commit: [프로젝트명]"
git branch -M main
git remote add origin https://github.com/[계정]/[레포명].git
git push -u origin main
```

### 흔한 오류 대처
| 오류 | 원인 | 해결 |
|---|---|---|
| `src refspec main does not match` | 커밋 없음 | `git add .` → `git commit` 먼저 |
| `fetch first` | GitHub에 자동 생성 파일 있음 | `git push --force` |
| 폴더가 안 올라감 | gitignore 패턴이 내용물을 제외 | `!폴더명/` 예외 추가 |

---

## 6단계: 대용량 파일 공유
- **30MB 이하**: Git LFS 사용 가능
- **30MB 이상**: Google Drive 업로드 후 README에 링크
  ```markdown
  → [📥 파일 다운로드](https://drive.google.com/...)
  ```

---

## 이후 업데이트 방법
```bash
git add [파일명]
git commit -m "Update: 변경 내용 설명"
git push
```
