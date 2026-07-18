import os
import glob

base_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../.."))
log_files = glob.glob(f"{base_dir}/SG_proj_*/development_log.txt") + glob.glob(f"{base_dir}/SG_integration_*/development_log.txt")

english_log = """
---
Date: 2026-07-14
Author: Antigravity

[Updates]
- Hardware Specs updated in README.md from RTX 5080/Windows to Apple M2 Pro/macOS.
- Completed all local E2E and unit tests on macOS successfully without abort traps.
- Verified GitHub Actions CI/CD workflows for the projects.
"""

korean_log = """
## [2026-07-14]
[작업 요약] 리드미 스펙 변경 및 macOS 환경 점검 완료
[상세 내용]
1. README.md 하드웨어 스펙 변경
   - Windows/RTX 5080 환경에서 Apple M2 Pro (MacBook Pro 14 2023, 16GB Memory)로 일괄 수정
2. macOS 로컬 테스트 및 CI/CD 점검
   - 로컬 E2E 테스트 및 단위 테스트 통과 (Abort trap 에러 미발생)
   - GitHub Actions CI/CD 파이프라인 런타임 유효성 재확인 완료
"""

for l_file in log_files:
    if os.path.exists(l_file):
        with open(l_file, "r", encoding="utf-8") as f:
            content = f.read()
        
        if english_log in content:
            content = content.replace(english_log, korean_log)
            with open(l_file, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"Fixed log in {l_file}")
