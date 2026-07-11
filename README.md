# 위클리 마켓 리뷰

국내 증시(코스피/코스닥) 주간 뉴스와 바닥권 반등 종목을 정리하는
자동 발행 매거진. 매주 GitHub Actions가 Claude API로 그 주를 조사해
새 호를 만들고, GitHub Pages로 바로 볼 수 있습니다.

## 폴더 구조

```
index.html              # 아카이브(전체 호 목록) 페이지
issues/
  manifest.json          # 발행된 호 목록 (issue_no, 파일명, 제목, 날짜)
  2026-07-11.html         # 개별 호
assets/style.css         # 모든 페이지 공용 스타일
scripts/generate_issue.py # Claude API로 새 호를 만드는 스크립트
.github/workflows/weekly-magazine.yml  # 매주 자동 실행
```

## 처음 설정하는 법

1. **이 폴더를 새 GitHub 저장소로 올리기** (예: `market-magazine`)
   ```bash
   git init
   git add .
   git commit -m "init"
   git branch -M main
   git remote add origin https://github.com/<본인계정>/market-magazine.git
   git push -u origin main
   ```

2. **API 키 등록**
   저장소 → Settings → Secrets and variables → Actions → New repository secret
   - Name: `ANTHROPIC_API_KEY`
   - Value: (본인 Anthropic API 키, console.anthropic.com에서 발급)

3. **GitHub Pages 켜기**
   저장소 → Settings → Pages → Source를 `Deploy from a branch`로,
   Branch를 `main` / `/ (root)`로 설정. 몇 분 뒤
   `https://<본인계정>.github.io/market-magazine/` 에서 확인 가능.

4. **자동 발행 확인**
   `.github/workflows/weekly-magazine.yml`이 매주 토요일 오전 7시(KST)에
   자동 실행되어 `issues/`에 새 파일을 추가하고 `manifest.json`을
   업데이트한 뒤 커밋·푸시합니다. 바로 테스트해보고 싶으면 저장소의
   Actions 탭 → Weekly Market Magazine → Run workflow로 즉시 실행 가능.

## 지난 호 찾아보기

`index.html`이 `issues/manifest.json`을 읽어 자동으로 아카이브 목록을
만들어 보여줍니다. 새 호가 추가될 때마다 별도 작업 없이 목록에 반영됩니다.

## 디자인/내용을 바꾸고 싶다면

- 전체 톤/문구 스키마: `scripts/generate_issue.py`의 `SCHEMA_INSTRUCTIONS`
- 시각 디자인(색상, 폰트, 레이아웃): `assets/style.css`
- 발행 주기: `.github/workflows/weekly-magazine.yml`의 `cron` 값

## 참고

- 이 저장소는 매주 실제 웹 검색 결과를 바탕으로 Claude가 내용을 채웁니다.
  투자 권유가 아닌 정보 정리이며, 투자 판단의 책임은 본인에게 있습니다.
- Anthropic 모델 이름은 시간이 지나며 바뀔 수 있습니다. 스크립트가 실패하면
  `scripts/generate_issue.py`의 `MODEL` 값을
  [Anthropic 문서](https://docs.claude.com)에서 최신 모델 ID로 업데이트하세요.
