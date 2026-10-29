# 초식남녀 AI 단편 애니메이션 〈만나기까지, 일주일〉

- 길이: 약 87초 (16:9, 1920×1080)
- 분위기: 조용하고 따뜻한 대학생 로맨스
- 그림체: 굵은 검은 외곽선과 평면 색을 쓰는 미국 TV 시트콤 애니메이션 스타일, 색감은 따뜻하게
- 핵심 메시지: 조심스러운 사람에게도 인연을 시작할 방법은 필요하다.
- 제작 분담: 사람이 나오는 장면 10컷은 AI 영상 도구로 생성, 휴대폰 화면 6컷과 엔딩은 Claude가 그래픽으로 제작(한글이 깨지지 않도록), 편집·자막·음악은 Claude가 마무리

---

## 1. 먼저 만들 것: 두 인물의 기준 이미지 (10분)

ChatGPT, Gemini 같은 이미지 생성 도구에서 아래 프롬프트로 인물마다 한 장씩 만듭니다. 마음에 드는 결과를 골라 `ref_jiho.png`, `ref_seoyeon.png`로 저장하고, 모든 AI 컷을 **이미지 → 영상** 방식으로 만들 때 첫 프레임이나 참고 이미지로 넣습니다. 이렇게 해야 컷마다 얼굴이 바뀌지 않아요.

### 그림체 공통 문구 (모든 프롬프트 끝에 붙이기)
```
2D adult animated sitcom style, thick uniform black outlines, flat cel-shaded colors with very little shading, simple rounded shapes, large oval white eyes with small black pupils, rounded chin, simple four-finger hands, clean vector look, warm soft color palette, calm and cozy mood, 16:9, no text, no letters, no logos, no watermark
```

### 주인공 지호 (남)
```
Character reference sheet of an original character: a shy Korean university student in his early 20s, short messy black hair, round black glasses, mustard-yellow hoodie, dark blue jeans, white sneakers, gray backpack, slightly hunched posture, gentle nervous smile. Full body, front view and three-quarter view, plain light background. [그림체 공통 문구]
```

### 상대 서연 (여)
```
Character reference sheet of an original character: a quiet Korean university student in her early 20s, shoulder-length brown hair with straight bangs, sage-green cardigan over a white T-shirt, long beige skirt, canvas tote bag, small round earrings, soft shy smile. Full body, front view and three-quarter view, plain light background. [그림체 공통 문구]
```

> 팁: 결과가 기존 애니메이션 캐릭터와 닮아 보이면 다시 만드세요. 우리 인물은 새로 만든 캐릭터여야 해요.

---

## 2. 컷 리스트 (총 17컷)

- **AI** = 영상 도구로 생성
- **UI** = Claude가 만드는 휴대폰 화면 컷

| # | 시간 | 종류 | 화면 | 내레이션 / 대사 / 소리 |
|---|------|------|------|------|
| 1 | 0:00–0:05 | AI | 캠퍼스 벤치에 혼자 앉은 지호, 멀리서 친구들이 웃고 있다 | 내레이션: 누군가를 만나고 싶었다. |
| 2 | 0:05–0:10 | UI | 메시지 "오늘 일일호프 갈래?" → 답장을 쓰다가 지운다 | 내레이션: 그런데 처음 다가가는 일은 늘 어려웠다. |
| 3 | 0:10–0:15 | AI | 밤, 자취방 책상. 지호가 휴대폰을 엎어 놓고 한숨 쉰다 | (조용한 방 소리) |
| 4 | 0:15–0:20 | UI | 친구 대화창 "소개해 줄 사람 생기면 알려줄게" | 내레이션: 소개를 부탁할 사람도, 선뜻 꺼낼 용기도 많지 않았다. |
| 5 | 0:20–0:25 | AI | 지호가 휴대폰을 다시 들어 보다가 눈이 커지고 살짝 웃는다 | 내레이션: 그러다 알게 된 곳이 있었다. |
| 6 | 0:25–0:32 | UI | 초식남녀 앱: 공룡 아이콘 → 학생증 촬영·인증 → "학생증 사진으로 AI가 매칭해요" → 이상형 설문 | 내레이션: 학생증으로 인증하고, 내가 바라는 사람을 이야기하면 먼저 소개해 주는 곳. |
| 7 | 0:32–0:37 | UI | "서로의 취향을 고려한 한 사람을 소개해 드려요" → 사진 없는 소개 카드 → 수락 | 알림음 |
| 8 | 0:37–0:42 | AI | 다른 방의 서연. 알림을 보고 잠시 망설이다 수락을 누르고 미소 짓는다 | 화면 자막: 서로 수락했어요. 일주일 동안 알아가 볼까요? |
| 9 | 0:42–0:47 | AI | 도서관의 지호. 메시지를 읽고 입꼬리가 올라간다 | 대사(자막): 오늘 수업 어땠어요? |
| 10 | 0:47–0:52 | AI | 버스 창가의 서연. 답장을 쓰며 웃는다 | 대사(자막): 발표했는데 엄청 떨었어요. |
| 11 | 0:52–0:57 | UI | 대화창 + DAY 1 → 3 → 6 | 대사(자막): 저도요. 끝나고 나서야 숨 쉬었어요. |
| 12 | 0:57–1:02 | AI | 밤, 방에서 휴대폰을 보며 소리 없이 웃는 지호 | (잔잔한 피아노) |
| 13 | 1:02–1:08 | UI | DAY 7 "직접 만나보고 싶나요?" → 둘 다 수락 → "토요일 오후, 카페에서 만나요" | 내레이션: 사진은 몰랐지만, 내 이야기를 기다려 주는 사람이라는 건 알게 됐다. |
| 14 | 1:08–1:13 | AI | 토요일 낮의 조용한 카페. 창가에 앉은 지호가 문 쪽을 본다 | (카페 소리) |
| 15 | 1:13–1:18 | AI | 지호의 어깨 너머로, 서연이 문을 열고 들어와 두리번거린다 | 대사(자막): 혹시… 초식남녀? |
| 16 | 1:18–1:23 | AI | 처음으로 두 사람이 같은 화면에. 마주 앉아 수줍게 웃는다 | 대사(자막): 네. 안녕하세요. |
| 17 | 1:23–1:27 | UI | 아이보리 배경에 크레파스 공룡과 '초식남녀' 로고 | 내레이션: 먼저 다가가는 건 저희가, 서로를 알아가는 건 우리가. |

- 대사는 입 모양이 맞지 않는 문제를 피하려고 **자막 + 목소리**로 넣습니다. 그래서 15·16컷은 말하는 입이 크게 보이지 않는 구도로 만들어요.
- AI가 완벽한 이상형이나 연애 성공을 보장한다는 표현은 쓰지 않아요.

---

## 3. AI 컷별 프롬프트 (영어, 복사해서 사용)

`[지호]`, `[서연]`에는 아래 짧은 묘사를, `[스타일]`에는 1번의 그림체 공통 문구를 넣습니다. 기준 이미지도 함께 넣으세요.

- `[지호]` = `Jiho, a shy Korean university student with short messy black hair, round black glasses and a mustard-yellow hoodie`
- `[서연]` = `Seoyeon, a quiet Korean university student with shoulder-length brown hair with bangs and a sage-green cardigan`

**컷 1** (5초)
```
Wide shot of a sunny university campus. [지호] sits alone on a wooden bench holding his phone, while a group of students laugh together far in the background. He glances at them, then looks down. Slow gentle push-in. [스타일]
```

**컷 3** (5초)
```
Night, a small studio room lit by a desk lamp. [지호] sits at his desk, places his phone face down, leans back and lets out a quiet sigh. Static camera, soft warm lamp light. [스타일]
```

**컷 5** (5초)
```
Close-up of [지호] at his desk at night, picking his phone back up. The screen's glow lights his face; his eyes widen a little and a small hopeful smile appears. The phone screen faces away from the camera. [스타일]
```

**컷 8** (5초)
```
A cozy bedroom in the evening. [서연] sits on her bed and looks at her phone after a notification, hesitates for a moment, then taps the screen and smiles shyly. The phone screen faces away from the camera. [스타일]
```

**컷 9** (5초)
```
A quiet university library with tall bookshelves. [지호] sits at a long table with an open book, reads a message on his phone and the corners of his mouth slowly lift. Soft afternoon light from the windows. [스타일]
```

**컷 10** (5초)
```
Inside a city bus by the window in the afternoon. [서연] types on her phone with both thumbs and smiles to herself, city streets passing by outside. Gentle swaying motion. [스타일]
```

**컷 12** (5초)
```
Night, [지호]'s small room. He lies on his bed looking at his phone and laughs quietly, covering his mouth with his hand. Warm lamp light, calm mood. [스타일]
```

**컷 14** (5초)
```
Saturday afternoon in a small quiet cafe with plants and wooden tables. [지호] sits alone by the window with a cup of coffee, nervously glancing toward the entrance door. Soft sunlight. [스타일]
```

**컷 15** (5초)
```
Over-the-shoulder shot from behind [지호] sitting at a cafe table. Across the room, [서연] opens the glass door, steps in and looks around carefully. Bell above the door swings. [스타일]
```

**컷 16** (5초)
```
Medium shot, the first time both characters appear together facing each other at a small cafe table by the window. [지호] and [서연] smile shyly and give a small wave hello. Warm golden afternoon light, calm happy mood. [스타일]
```

### 공통 부정 프롬프트 (도구에 입력란이 있으면)
```
text, letters, subtitles, logo, watermark, realistic photo, 3D render, extra fingers, distorted face, different character design, horror
```

---

## 4. 생성 팁

1. **도구:** Kling, Hailuo, Runway, Pika 등에서 '이미지 → 영상'을 쓰세요. 무료 크레딧이 모자라면 컷 1, 8, 15, 16을 먼저 만드세요. 이야기의 뼈대가 되는 장면이에요.
2. **첫 프레임 만들기:** 영상 도구에 넣을 첫 장면 이미지를 이미지 생성 도구에서 먼저 만드세요. 기준 이미지와 컷 프롬프트를 함께 넣고 "같은 캐릭터로 이 장면을 그려줘"라고 하면 돼요. 그 이미지를 영상 도구에 넣으면 인물이 가장 덜 바뀌어요.
3. **휴대폰 화면:** 화면이 카메라를 향하지 않게 만들었어요. 화면 내용은 UI 컷이 보여 줍니다.
4. **여러 번 생성하기:** 컷마다 2~3번 만들어 가장 자연스러운 것을 고르세요.
5. **저장 이름:** `cut01.mp4`, `cut03.mp4` …처럼 컷 번호로 저장해서 보내 주세요. 나머지 편집은 Claude가 합니다.

---

## 5. 내레이션 대본 (직접 녹음 추천)

조용히, 천천히 읽어 주세요. 휴대폰 음성 메모로 녹음해도 충분해요.

1. (0:00) 누군가를 만나고 싶었다.
2. (0:05) 그런데 처음 다가가는 일은 늘 어려웠다.
3. (0:15) 소개를 부탁할 사람도, 선뜻 꺼낼 용기도 많지 않았다.
4. (0:20) 그러다 알게 된 곳이 있었다.
5. (0:25) 학생증으로 인증하고, 내가 바라는 사람을 이야기하면 먼저 소개해 주는 곳.
6. (1:02) 사진은 몰랐지만, 내 이야기를 기다려 주는 사람이라는 건 알게 됐다.
7. (1:23) 먼저 다가가는 건 저희가, 서로를 알아가는 건 우리가.

대사(9·10·11·15·16컷)는 자막으로 넣고, 원하면 두 사람 목소리로도 녹음해요.

---

## 6. 보고서에 쓸 제작 기록

- 사용한 이미지·영상 생성 도구와 날짜
- 기준 이미지 프롬프트와 결과
- 컷별 생성 횟수, 실패했던 점(얼굴 변화, 손가락, 글자 등)과 해결 방법
- 내레이션 녹음 방식, 음악 출처
- 최종 길이와 해상도
