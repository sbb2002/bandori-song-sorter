# tools/wordcloud — 밴드 가사 → 키워드 추출

밴드별 조회수 TOP10 곡 가사(`assets/lyrics/<band>.md`)에서 **일본어 명사 빈도**를
뽑아 워드클라우드용 `src/content/wordcloud/<band>.yaml`(커밋·사용자 편집)을 생성한다.

HANDOFF #2(②안) 구현. 가사 **원문은 보관하지 않고** 단어 단위 키워드+빈도만 남긴다(저작권 회피).

## 구성
- `lyrics_parser.py` — `<band>.md` 파서. 줄별 문자종(일본어/한글)으로 분류해
  「원문(jp) / 음차 / 번안(ko)」 트리플렛과 곡 메타(url·views·cover)를 추출.
- `build_keywords.py` — 파이프라인 본체.
  1. fugashi+unidic-lite로 일본어 **명사** 추출(불용어·영어조각·단일가나 필터), 빈도 집계.
  2. **커버곡 제외**(밴드 고유 정체성 기준; `comment: Cover` 활용).
  3. ko 채우기: 가사의 **한글 번안**을 kiwipiepy 명사 + Dice 통계로 단어정렬 추정(우선) →
     실패 시 **기계번역**(deep-translator, eol 주석 `# 기계번역 초안`) → 그래도 없으면 빈칸.

## 사용
```bash
python -m pip install -r src/tools/wordcloud/requirements.txt
python src/tools/wordcloud/build_keywords.py            # 전 밴드 → src/content/wordcloud/*.yaml
python src/tools/wordcloud/build_keywords.py --debug    # yaml 미기록, 상위 명사 확인
python src/tools/wordcloud/build_keywords.py --band mygo --no-translate
```
주요 옵션: `--band <stem>` 특정 밴드 · `--min-weight N`(기본 2) · `--include-covers`
· `--no-translate`(MT 보완 끔) · `--debug`/`--top N`.

## 산출 yaml 스키마
```yaml
band: mygo
generated: 'YYYY-MM-DD'
song_count: 10          # 키워드 산출에 쓰인 곡 수(커버·빈 곡 제외)
keywords:
  - {jp: 心, ko: 마음, weight: 15}
  - {jp: 全て, ko: 모두, weight: 3}  # 기계번역 초안
```
`ko`/`weight`는 **사용자가 직접 수정·덮어쓰는 초안**이다. 공식 번역이 있으면 우선한다.

## 메모
- 콘솔 인코딩 이슈 시 `PYTHONUTF8=1 PYTHONIOENCODING=utf-8` 지정.
- 정렬표는 **전 밴드 (명사집합, 번안문) 쌍**을 모아 한 번에 구축(데이터 많을수록 정확).
- 원문 `<band>.md`는 `.gitignore`로 비커밋(저작권). 재생성을 위해 로컬에는 보관한다.
