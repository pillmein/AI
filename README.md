## Source code에 대한 설명
### 폴더 구조

```
📂 Frontend_Android
├── 📂 android : Android 빌드 설정
│   ├── 📂 app
│   ├── build.gradle
│   ├── gradle
│   ├── gradlew
│   └── settings.gradle
├── 📂 app : 앱 코드 (화면, 컴포넌트, API 등)
│   ├── App.tsx : 최상위 컴포넌트
│   ├── 📂 api
│   ├── 📂 assets
│   ├── 📂 components : 재사용 가능한 UI 컴포넌트들
│   ├── 📂 navigation : React Navigation 설정 (화면 이동 관련)
│   └── 📂 screens : 화면 단위 컴포넌트들
├── node_modules : 설치된 npm 패키지들
├── app.json
├── babel.config.js
├── eas.json
├── env.d.ts
├── eslint.config.mjs
├── index.ts
├── package.json
├── package-lock.json
├── tsconfig.json
└── yarn.lock
```

<br>

### 빌드 방식
EAS (Expo Managed Workflow 기반) 에서 이후 EAS Build 사용 / 네이티브 기능 추가하면서 Bare로 전환

---

### How to Install

<br>
1. Repository 클론
<br><br>

```
git clone https://github.com/pillmein/Frontend_Android.git
cd Frontend_Android
```

 <br>
 2. 의존성 설치
<br><br>

 ```
npm install
 ```
- git clone을 하면 의존성 패키지들이 없기 때문에 설치가 필요합니다. 
- 설치 완료 시 node_modules 폴더가 생성됩니다.

 <br>
3. 개발 서버 실행
<br><br>

```
npx expo start
```

### How to Build

<br>

```
npx expo run:android
```

- 빌드 파일이 android 폴더에 생성됩니다.

### How to Test

#### 주의
.gitignore에 포함된 .env 와 android/app/google-services.json 파일이 있어야 정상 실행 가능합니다.

<br>
로컬 환경에서 테스트
<br><br>

```
npx expo start
```

---

## Open Source

### Frontend Libraries & Tools

1. **React-native + Expo**: [React native Official Site](https://reactnative.dev/)
2. **Axios**: [Axios Official Site](https://axios-http.com/)
3. **Styled-components**: [Styled-components Official Site](https://styled-components.com/)
4. **Prettier**: [Prettier Official Site](https://prettier.io/)
5. **Eslint**: [Eslint Official Site](https://eslint.org/)
