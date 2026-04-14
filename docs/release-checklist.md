# Release checklist

so2x-harness의 0.1.x 릴리즈를 준비할 때 확인할 최소 체크리스트입니다.

## Release goal
- install/apply/update/doctor의 기본 흐름이 깨지지 않는다.
- README의 사용 예시가 현재 동작과 맞는다.
- 샘플 프로젝트 기준으로 최소 한 번 재검증한다.

## Before version bump
- [ ] `main` 브랜치가 최신 상태다.
- [ ] 릴리즈에 포함할 범위가 issue 기준으로 정리돼 있다.
- [ ] 미완성 실험 코드가 포함되지 않았다.

## Functional checks
- [ ] `python3 scripts/apply.py --project <test-project> --platform claude` 실행 확인
- [ ] `python3 scripts/update.py --project <test-project>` 실행 확인
- [ ] `python3 scripts/doctor.py --project <empty-project>` 실행 확인
- [ ] `python3 scripts/doctor.py --project <installed-project>` 실행 확인
- [ ] `./install.sh <test-project>` 실행 확인

## Documentation checks
- [ ] README의 install 예시가 최신이다.
- [ ] README의 update 예시가 최신이다.
- [ ] README의 doctor 예시가 최신이다.
- [ ] 새 기능이 있으면 examples 또는 materials에도 반영했다.

## Versioning
- [ ] `VERSION` 파일을 새 버전으로 올렸다.
- [ ] 필요하면 `harness.yaml`의 version도 함께 확인했다.
- [ ] 릴리즈 메시지에 핵심 변경사항 3~5개를 요약할 수 있다.

## Git hygiene
- [ ] working tree가 깨끗하다.
- [ ] 불필요한 generated file이 커밋되지 않았다.
- [ ] 커밋 메시지가 변경 범위를 설명한다.

## Tag and release
예시:

```bash
git pull origin main
git status
printf '0.1.1\n' > VERSION
git add VERSION
git commit -m "버전 0.1.1 준비"
git push origin main
git tag v0.1.1
git push origin v0.1.1
```

## Suggested release notes format

```md
## so2x-harness v0.1.1

### What changed
- install script usability improvements
- doctor command baseline checks
- skill quality upgrades

### Validation
- apply/update/doctor tested on sample project
- install.sh tested on local sample path

### Notes
- Claude-only support in v0.1.x
```
