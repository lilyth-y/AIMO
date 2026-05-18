# AIMO 대시보드 GitHub Pages 배포 가이드

본 문서는 Vite + React 기반의 **AIMO 발표용 대시보드**를 GitHub Pages에 배포하기 위해 수행된 설정 변경 사항 및 실제 배포 활성화 방법을 설명합니다.

---

## 1. 주요 배포 설정 및 변경 사항

정적 웹 호스팅 환경(GitHub Pages)은 기본적으로 서브디렉터리 경로(예: `https://<username>.github.io/AIMO/`)를 사용하므로, 로컬의 루트 경로(`/`) 기준 설정을 동적으로 변경해 주어야 합니다. 이를 위해 아래의 작업들이 적용되었습니다.

### A. 동적 Base URL 적용 (`dashboard/vite.config.js`)
* **설정**: 개발 모드(`mode === 'development'`)에서는 루트 경로(`/`)로 작동하며, 배포용 빌드 모드(`mode === 'production'`)일 때만 자동으로 `/AIMO/`를 기준 경로로 설정하도록 수정하였습니다.
* **코드 내용**:
  ```javascript
  base: mode === 'production' ? '/AIMO/' : '/',
  ```

### B. React Router Basename 설정 (`dashboard/src/main.tsx`)
* **설정**: GitHub Pages의 서브디렉터리 호스팅 구조 하에서 React Router가 정상 작동하고 빈 화면(Blank)이나 404가 발생하지 않도록 `<BrowserRouter>`에 `basename` 속성을 추가했습니다.
* **코드 내용**:
  ```typescript
  <BrowserRouter basename={import.meta.env.BASE_URL}>
  ```

### C. 파일 가져오기(Fetch) 경로 동적화
컴파일 타임에 번들링되지 않는 정적 파일(예: balanced 데이터셋 JSON, 모델 결과 JSON 등)들을 올바른 서브폴더에서 가져올 수 있도록 모든 API fetch 호출 앞에 `import.meta.env.BASE_URL`을 접두사로 붙였습니다.
* **적용 파일**:
  * [Accuracy.tsx](file:///c:/startingup/AIMO/dashboard/src/pages/Accuracy.tsx) (`/results/numina_balanced_results.json`)
  * [Comparison.tsx](file:///c:/startingup/AIMO/dashboard/src/pages/Comparison.tsx) (`/results/comparison_data.json`)
  * [ProblemViewer.tsx](file:///c:/startingup/AIMO/dashboard/src/pages/ProblemViewer.tsx) (`/numina_eval_balanced.json`, `/numina_5k.json`, 결과 데이터 등)
  * [Process.tsx](file:///c:/startingup/AIMO/dashboard/src/pages/Process.tsx) (`/numina_eval_balanced.json`, `/eval_data.json`)

### D. Live AI 연동 엔드포인트 동적화 (`dashboard/src/pages/LiveSolve.tsx`)
* **설정**: 실시간 LLM 추론 연동(`LiveSolve`) 시 고정된 로컬 주소(`/api/solve/stream`) 대신 환경 변수 `import.meta.env.VITE_API_URL`을 주입받아 동적으로 외부의 FastAPI 서버 주소를 바라볼 수 있도록 개선했습니다. (로컬 개발 환경에서는 기존 프록시로 동작하도록 폴백 유지)

### E. GitHub Actions 자동화 워크플로우 추가 (`.github/workflows/deploy-dashboard.yml`)
* **동작**: `changes` 혹은 `master` 브랜치에 코드가 push되거나, 수동으로 Actions를 구동(`workflow_dispatch`)하면 자동으로 Node.js 환경에서 의존성을 설치하고 대시보드를 빌드하여 `gh-pages` 브랜치에 배포합니다.

---

## 2. GitHub Pages 활성화 방법 (저장소 설정)

GitHub Actions 워크플로우를 생성했으므로, 원격 저장소(`github.com/lilyth-y/AIMO`)에 코드를 푸시한 후 아래 설정을 완료해야 최종 배포가 완료됩니다.

1. **코드 푸시**:
   현재 수정한 브랜치(`changes` 또는 `master`)의 변경 사항을 원격 저장소로 푸시합니다.
   ```bash
   git add .
   git commit -m "feat: configure vite dashboard deployment to GitHub Pages"
   git push origin <your-branch-name>
   ```

2. **GitHub Actions 실행 대기**:
   * GitHub 저장소 페이지의 **[Actions]** 탭으로 이동합니다.
   * `Deploy Dashboard to GitHub Pages` 워크플로우가 자동으로 실행되어 성공(`Green Check`)으로 끝날 때까지 대기합니다. (성공 시 원격 저장소에 `gh-pages` 브랜치가 자동 생성됩니다.)

3. **GitHub Pages 설정 활성화**:
   * GitHub 저장소의 **[Settings]** 탭으로 이동합니다.
   * 좌측 사이드바의 **[Pages]** 메뉴를 선택합니다.
   * **Build and deployment** 섹션의 **Source**가 `Deploy from a branch`로 선택되어 있는지 확인합니다.
   * **Branch** 설정을 `None`에서 `gh-pages` 브랜치로 변경하고, 대상 폴더를 `/ (root)`로 지정한 뒤 **[Save]**를 클릭합니다.

4. **배포 확인**:
   * 설정이 완료되면 상단에 **"Your site is live at..."**와 함께 배포된 URL 주소가 나타납니다.
   * 잠시 후 `https://lilyth-y.github.io/AIMO/` 주소로 접속하면 정상적으로 실행되는 AIMO 대시보드를 확인하실 수 있습니다!

---

## 3. 로컬에서 변경된 빌드 검증

로컬에서 실제 프로덕션 빌드가 통과하는지 사전 검증을 마쳤습니다. `npm run build` 구동 결과:
```bash
vite v5.4.21 building for production...
✓ 1066 modules transformed.
dist/index.html                                           0.42 kB
dist/assets/index-C67zKrHW.css                           80.19 kB
dist/assets/index-BGHoWwV3.js                         1,053.09 kB
✓ built in 4.66s
```
모든 리소스 번들링 및 정적 최적화 파일 생성이 완벽히 정상 작동함을 확인했습니다.
