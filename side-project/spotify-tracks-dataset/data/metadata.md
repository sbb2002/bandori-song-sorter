# About Dataset

## Content
This is a dataset of Spotify tracks over a range of 125 different genres. Each track has some audio features associated with it. The data is in CSV format which is tabular and can be loaded quickly.

## Usage
The dataset can be used for:

* Building a Recommendation System based on some user input or preference
* Classification purposes based on audio features and available genres
* Any other application that you can think of. Feel free to discuss!

## Column Description
- track_id: The Spotify ID for the track
- artists: The artists' names who performed the track. If there is more than one artist, they are separated by a ;
- album_name: The album name in which the track appears
- track_name: Name of the track
- popularity: The popularity of a track is a value between 0 and 100, with 100 being the most popular. The popularity is calculated by algorithm and is based, in the most part, on the total number of plays the track has had and how recent those plays are. Generally speaking, songs that are being played a lot now will have a higher popularity than songs that were played a lot in the past. Duplicate tracks (e.g. the same track from a single and an album) are rated independently. Artist and album popularity is derived mathematically from track popularity.
- duration_ms: The track length in milliseconds
- explicit: Whether or not the track has explicit lyrics (true = yes it does; false = no it does not OR unknown)
- danceability: Danceability describes how suitable a track is for dancing based on a combination of musical elements including tempo, rhythm stability, beat strength, and overall regularity. A value of 0.0 is least danceable and 1.0 is most danceable
- energy: Energy is a measure from 0.0 to 1.0 and represents a perceptual measure of intensity and activity. Typically, energetic tracks feel fast, loud, and noisy. For example, death metal has high energy, while a Bach prelude scores low on the scale
- key: The key the track is in. Integers map to pitches using standard Pitch Class notation. E.g. 0 = C, 1 = C♯/D♭, 2 = D, and so on. If no key was detected, the value is -1
- loudness: The overall loudness of a track in decibels (dB)
- mode: Mode indicates the modality (major or minor) of a track, the type of scale from which its melodic content is derived. Major is represented by 1 and minor is 0
- speechiness: Speechiness detects the presence of spoken words in a track. The more exclusively speech-like the recording (e.g. talk show, audio book, poetry), the closer to 1.0 the attribute value. Values above 0.66 describe tracks that are probably made entirely of spoken words. Values between 0.33 and 0.66 describe tracks that may contain both music and speech, either in sections or layered, including such cases as rap music. Values below 0.33 most likely represent music and other non-speech-like tracks
- acousticness: A confidence measure from 0.0 to 1.0 of whether the track is acoustic. 1.0 represents high confidence the track is acoustic
- instrumentalness: Predicts whether a track contains no vocals. "Ooh" and "aah" sounds are treated as instrumental in this context. Rap or spoken word tracks are clearly "vocal". The closer the instrumentalness value is to 1.0, the greater likelihood the track contains no vocal content
- liveness: Detects the presence of an audience in the recording. Higher liveness values represent an increased probability that the track was performed live. A value above 0.8 provides strong likelihood that the track is live
- valence: A measure from 0.0 to 1.0 describing the musical positiveness conveyed by a track. Tracks with high valence sound more positive (e.g. happy, cheerful, euphoric), while tracks with low valence sound more negative (e.g. sad, depressed, angry)
- tempo: The overall estimated tempo of a track in beats per minute (BPM). In musical terminology, tempo is the speed or pace of a given piece and derives directly from the average beat duration
- time_signature: An estimated time signature. The time signature (meter) is a notational convention to specify how many beats are in each bar (or measure). The time signature ranges from 3 to 7 indicating time signatures of 3/4, to 7/4.
- track_genre: The genre in which the track belongs

## 변수 분류 (오디오 분석 파이프라인 관점)

Spotify 오디오 분석은 보통 "신호에서 직접 측정 → 저수준 값들을 조합한 서술적 지표 → 오디오와 무관한 별도 알고리즘/모델 예측"의 단계를 거친다. 이 관점에서 컬럼을 세 그룹으로 나누면 다음과 같다.

### 1. 오디오 신호에서 직접 추출한 저수준(low-level) 변수
신호처리(비트 트래킹, 피치 검출, 라우드니스 측정 등)로 파형에서 곧바로 측정되는 값.
- `duration_ms` — 파형 길이
- `key` — 피치 클래스 추정(조성)
- `mode` — 장/단조 판별
- `loudness` — dB 단위 라우드니스
- `tempo` — 비트 트래킹으로 얻은 BPM
- `time_signature` — 박자 추정

### 2. 저수준 변수를 조합해 만든 합성(고수준 서술적) 변수
위 저수준 값들과 스펙트럴/리듬 특성을 결합해 계산하는 0.0~1.0 스케일의 서술적 지표. (참고: Spotify 자체는 이 값들도 내부적으로 학습된 모델로 산출하지만, 본 데이터셋 관점에서는 "오디오 특성들을 조합한 2차 지표"로 분류)
- `danceability` — tempo·리듬 안정성·비트 강도 등의 조합
- `energy` — loudness·음색·구간별 강도 조합
- `speechiness` — 스펙트럴 특성 기반 음성 존재도
- `acousticness` — 스펙트럴 특성 기반 어쿠스틱 신뢰도
- `instrumentalness` — 보컬 유무 추정
- `liveness` — 청중/라이브 녹음 여부 추정
- `valence` — 위 요소들을 종합한 긍정성/분위기 지표

### 3. 오디오 특성이 아닌 별도 알고리즘/모델로 예측한 변수
오디오 신호 분석이 아니라 사용 데이터나 메타데이터 기반 알고리즘으로 산출되는 값.
- `popularity` — 재생 횟수와 최신성을 기반으로 한 알고리즘 산출값 (오디오 분석과 무관)
- `track_genre` — 이 데이터셋에서는 수집 시 지정한 태그로 보이나, 서비스 맥락에서는 분류 모델로 예측되기도 하므로 참고용으로 분류

### 분류 대상 아님 (원본 메타데이터)
- `track_id`, `artists`, `album_name`, `track_name`, `explicit` — 오디오 분석과 무관한 카탈로그 메타데이터