# i18n Spanish Translation Implementation Plan

## Files to Create

### 1. `/frontend/src/i18n.ts` - i18n Configuration
```typescript
import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import translationES from './locales/es/translation.json';

const resources = {
    es: {
        translation: translationES,
    },
};

i18n
    .use(initReactI18next)
    .init({
        resources,
        lng: 'es',
        fallbackLng: 'es',
        interpolation: {
            escapeValue: false,
        },
    });

export default i18n;
```

### 2. `/frontend/src/locales/es/translation.json` - Spanish Translations
```json
{
    "app": {
        "title": "Tài Sī - Conversación por Voz",
        "wakingUp": "Despertando a TARS...",
        "preparingRoleplay": "Preparando roleplay..."
    },
    "header": {
        "level": "NIVEL 24 • AVANZADO",
        "days": "12 DÍAS"
    },
    "bottomNav": {
        "home": "Inicio",
        "roleplay": "Roleplay",
        "profile": "Perfil"
    },
    "modeCards": {
        "normalMode": "MODO NORMAL",
        "normalSubtitle": "Domina el vocabulario y la gramática",
        "roleplayMode": "MODO ROLEPLAY",
        "roleplaySubtitle": "Simulación de diálogo interactivo"
    },
    "micButton": {
        "holdToActivate": "MANTÉN PARA ACTIVAR…",
        "holdToSpeak": "MANTÉN PARA HABLAR",
        "releaseToCancel": "SUELTA PARA CANCELAR",
        "normalMode3sec": "MODO NORMAL · 3 SEGUNDOS"
    },
    "loadingScreen": {
        "tars": "TARS",
        "wakingUp": "Despertando a TARS...",
        "toastName": "TARS"
    },
    "settings": {
        "title": "Configuración",
        "account": "Cuenta",
        "profile": "Perfil",
        "profileSub": "Información personal y objetivos",
        "subscription": "Suscripción",
        "proActive": "Tài Sī Pro • Activo",
        "preferences": "Preferencias",
        "targetLanguage": "Idioma objetivo",
        "mandarin": "Mandarín (Simplificado)",
        "voiceSpeed": "Velocidad de voz",
        "normal": "Normal",
        "display": "Pantalla",
        "lightMode": "Modo claro",
        "darkMode": "Modo oscuro",
        "logOut": "Cerrar sesión",
        "version": "Tài Sī v2.4.0 • Diseñado para concentrarte"
    },
    "roleplay": {
        "customScenarios": "Escenarios personalizados",
        "uploadDocument": "Subir nuevo documento",
        "supportedFormats": "Formatos: PDF, DOCX, TXT (Máx. 10MB)",
        "knowledgeBase": "Tu base de conocimiento",
        "files": "Archivos",
        "loadingFiles": "Cargando tus archivos...",
        "recentlyUploaded": "Subido recientemente",
        "scenario": "ESCENARIO",
        "startSession": "Iniciar sesión",
        "setUpRoles": "Configurar roles",
        "yourRole": "Tu personaje",
        "tarsRole": "Personaje de TARS",
        "placeholderCustomer": "ej. Cliente",
        "placeholderBarista": "ej. Barista"
    },
    "profile": {
        "title": "Perfil del Estudiante",
        "level": "Nvl 42",
        "imperialScholar": "Estudiante Imperial",
        "mandarinMaster": "Maestro del Mandarín",
        "hoursSpoken": "Horas habladas",
        "hoursUnit": "h",
        "thisMonth": "12% este mes",
        "mastery": "Dominio",
        "masteryUnit": "%",
        "hskLevel": "Nivel HSK 5",
        "currentStreak": "Racha actual",
        "streakUnit": "d",
        "topStreak": "Top 1% en racha",
        "vocabulary": "Vocabulario",
        "thisWeek": "+150 esta semana"
    },
    "personalInfo": {
        "title": "Información personal",
        "uploadPhoto": "Subir foto de perfil",
        "fullName": "Nombre completo",
        "yourName": "Tu nombre",
        "nativeLanguage": "Idioma nativo",
        "english": "Inglés",
        "french": "Francés",
        "german": "Alemán",
        "spanish": "Español",
        "hskLevel": "Nivel HSK actual",
        "hsk1": "HSK 1 (Principiante)",
        "hsk2": "HSK 2 (Elemental)",
        "hsk3": "HSK 3 (Intermedio)",
        "hsk4": "HSK 4 (Intermedio alto)",
        "hsk5": "HSK 5 (Avanzado)",
        "hsk6": "HSK 6 (Competente)",
        "learningGoals": "Objetivos de aprendizaje",
        "travel": "Viaje",
        "business": "Negocios",
        "academic": "Académico",
        "hobby": "Pasatiempo / Cultural",
        "interests": "Intereses",
        "saveChanges": "Guardar cambios"
    },
    "signIn": {
        "welcomeBack": "Bienvenido de nuevo",
        "subtitle": "Continúa tu camino hacia la fluidez.",
        "email": "Correo electrónico",
        "password": "Contraseña",
        "forgotPassword": "¿Olvidaste tu contraseña?",
        "signIn": "Iniciar sesión",
        "orContinueWith": "o continúa con",
        "continueWithGoogle": "Continuar con Google",
        "noAccount": "¿No tienes cuenta?",
        "createAccount": "Crea una ahora"
    },
    "signUp": {
        "joinAcademy": "Únete a la <accent>Academia</accent>",
        "subtitle": "Ingresa tus datos para comenzar tu camino hacia la concentración profunda.",
        "fullName": "Nombre completo",
        "placeholderName": "Maestro Confucio",
        "email": "Correo electrónico",
        "password": "Contraseña",
        "createAccount": "Crear cuenta",
        "masteryAwaits": "El dominio te espera",
        "hasAccount": "¿Ya tienes cuenta?",
        "signIn": "Iniciar sesión"
    },
    "forgotPassword": {
        "title": "¿Olvidaste tu <accent>Contraseña?</accent>",
        "subtitle": "No te preocupes, nos pasa a todos. Ingresa tu correo electrónico para recibir un enlace de restablecimiento de contraseña.",
        "email": "Correo electrónico",
        "sendLink": "Enviar enlace",
        "rememberPassword": "¿Recuerdas tu contraseña?",
        "logIn": "Iniciar sesión"
    },
    "conversation": {
        "normalModeActive": "Modo normal · Activo",
        "roleplayModeActive": "Modo roleplay · Activo",
        "connecting": "Conectando…",
        "speechNotSupported": "El reconocimiento de voz no es compatible con este navegador.",
        "hidePinyin": "Ocultar Pinyin",
        "showPinyin": "Aa Pinyin",
        "hideTranslate": "Ocultar traducción",
        "showTranslate": "A文 Traducción",
        "replaying": "Reproduciendo...",
        "repeat": "🔁 Repetir",
        "placeholder": "Escribe o habla…"
    },
    "voiceConversation": {
        "listening": "Escuchando...",
        "transcribing": "Transcribiendo audio...",
        "processing": "Procesando...",
        "back": "← Atrás",
        "focus": "Concentración",
        "roleplay": "Roleplay",
        "couldNotHear": "No pude escucharte claramente.",
        "connectionError": "Error de conexión:",
        "serverFailed": "El servidor falló",
        "micRequired": "Se requiere acceso al micrófono para hablar con Tars.",
        "repeatPhrase": "Repetir frase",
        "transcriptHistory": "Historial de transcripción"
    },
    "conversationContainer": {
        "error": "Error de Tars:",
        "socketReconnecting": "Socket no abierto, reconectando...",
        "reconnectFailed": "Reconexión fallida"
    },
    "common": {
        "tars": "TARS",
        "taisi": "Tài Sī"
    }
}
```

## Files to Modify

### 3. `/frontend/src/main.tsx`
Add i18n import before App:
```typescript
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './i18n'  // ADD THIS LINE
import './index.css'
import App from './App.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
```

### 4. `/frontend/index.html`
Change `<html lang="en">` to `<html lang="es">`
Change `<title>Tài Sī - Voice Conversation</title>` to `<title>Tài Sī - Conversación por Voz</title>`

### 5. All Component Files (18 files)
Each component needs:
1. Import: `import { useTranslation } from 'react-i18next';`
2. Hook: `const { t } = useTranslation();`
3. Replace all hardcoded strings with `t('key.path')`

## Component-by-Component Changes

### App.tsx
- Line 139: `"Waking up TARS..."` → `t('app.wakingUp')`
- Line 147: `"Preparing roleplay..."` → `t('app.preparingRoleplay')`

### Header.tsx
- Line 18: `"LEVEL 24 • ADVANCED"` → `t('header.level')`
- Line 32: `"12 DAYS"` → `t('header.days')`

### BottomNav.tsx
- Line 27: `"Home"` → `t('bottomNav.home')`
- Line 43: `"Roleplay"` → `t('bottomNav.roleplay')`
- Line 56: `"Profile"` → `t('bottomNav.profile')`

### ModeCards.tsx
- Line 20: `"NORMAL MODE"` → `t('modeCards.normalMode')`
- Line 21: `"Master the vocabulary & grammar"` → `t('modeCards.normalSubtitle')`
- Line 34: `"ROLEPLAY MODE"` → `t('modeCards.roleplayMode')`
- Line 35: `"Interactive dialogue simulation"` → `t('modeCards.roleplaySubtitle')`

### MicButton.tsx
- Line 86: `'HOLD TO ACTIVATE…'` → `t('micButton.holdToActivate')`
- Line 86: `'HOLD TO SPEAK'` → `t('micButton.holdToSpeak')`
- Line 89: `'RELEASE TO CANCEL'` → `t('micButton.releaseToCancel')`
- Line 89: `'NORMAL MODE · 3 SECONDS'` → `t('micButton.normalMode3sec')`

### LoadingScreen.tsx
- Line 16: `'Waking up TARS...'` → `t('loadingScreen.wakingUp')`
- Line 58: `"TARS"` → `t('loadingScreen.toastName')`
- Line 76: `"TARS"` → `t('loadingScreen.tars')`

### SettingsScreen.tsx
- Line 19: `"Settings"` → `t('settings.title')`
- Line 27: `"Account"` → `t('settings.account')`
- Line 34: `"Profile"` → `t('settings.profile')`
- Line 35: `"Personal information & goals"` → `t('settings.profileSub')`
- Line 44: `"Subscription"` → `t('settings.subscription')`
- Line 45: `"Tài Sī Pro • Active"` → `t('settings.proActive')`
- Line 54: `"Preferences"` → `t('settings.preferences')`
- Line 61: `"Target Language"` → `t('settings.targetLanguage')`
- Line 62: `"Mandarin (Simplified)"` → `t('settings.mandarin')`
- Line 71: `"Voice Speed"` → `t('settings.voiceSpeed')`
- Line 76: `"Normal"` → `t('settings.normal')`
- Line 85: `"Display"` → `t('settings.display')`
- Line 93: `'Light Mode'` / `'Dark Mode'` → `t('settings.lightMode')` / `t('settings.darkMode')`
- Line 109: `"Log Out"` → `t('settings.logOut')`
- Line 111: `"Tài Sī v2.4.0 • Built for focus"` → `t('settings.version')`

### RoleplayScreen.tsx
- Line 56: `"Custom Scenarios"` → `t('roleplay.customScenarios')`
- Line 69: `"Upload New Document"` → `t('roleplay.uploadDocument')`
- Line 72: `"Supported: PDF, DOCX, TXT (Max 10MB)"` → `t('roleplay.supportedFormats')`
- Line 78: `"Your Knowledge Base"` → `t('roleplay.knowledgeBase')`
- Line 79: `Files` → `t('roleplay.files')`
- Line 84: `"Loading your files..."` → `t('roleplay.loadingFiles')`
- Line 100: `"Recently Uploaded"` → `t('roleplay.recentlyUploaded')`
- Line 110: `"SCENARIO"` → `t('roleplay.scenario')`
- Line 116, 166: `"Start Session"` → `t('roleplay.startSession')`
- Line 135: `"Set up roles"` → `t('roleplay.setUpRoles')`
- Line 142: `"Your character role"` → `t('roleplay.yourRole')`
- Line 147: `"e.g. Customer"` → `t('roleplay.placeholderCustomer')`
- Line 151: `"TARS character role"` → `t('roleplay.tarsRole')`
- Line 156: `"e.g. Barista"` → `t('roleplay.placeholderBarista')`

### ProfileScreen.tsx
- Line 20: `"Scholar Profile"` → `t('profile.title')`
- Line 39: `"Lvl 42"` → `t('profile.level')`
- Line 44: `"Imperial Scholar"` → `t('profile.imperialScholar')`
- Line 47: `"Mandarin Master"` → `t('profile.mandarinMaster')`
- Line 56: `"Hours Spoken"` → `t('profile.hoursSpoken')`
- Line 57: `"h"` → `t('profile.hoursUnit')`
- Line 60: `"12% this month"` → `t('profile.thisMonth')`
- Line 66: `"Mastery"` → `t('profile.mastery')`
- Line 67: `"%"` → `t('profile.masteryUnit')`
- Line 70: `"HSK 5 Level"` → `t('profile.hskLevel')`
- Line 76: `"Current Streak"` → `t('profile.currentStreak')`
- Line 77: `"d"` → `t('profile.streakUnit')`
- Line 80: `"Top 1% streak"` → `t('profile.topStreak')`
- Line 86: `"Vocabulary"` → `t('profile.vocabulary')`
- Line 90: `"+150 this week"` → `t('profile.thisWeek')`

### PersonalInfoScreen.tsx
- Line 17: `"Personal Info"` → `t('personalInfo.title')`
- Line 38: `"Upload Profile Photo"` → `t('personalInfo.uploadPhoto')`
- Line 46: `"Full Name"` → `t('personalInfo.fullName')`
- Line 52: `"Your Name"` → `t('personalInfo.yourName')`
- Line 59: `"Native Language"` → `t('personalInfo.nativeLanguage')`
- Line 62-65: Language options → `t('personalInfo.english')`, etc.
- Line 72: `"Current HSK Level"` → `t('personalInfo.hskLevel')`
- Line 75-80: HSK levels → `t('personalInfo.hsk1')`, etc.
- Line 87: `"Learning Goals"` → `t('personalInfo.learningGoals')`
- Line 90-93: Goals → `t('personalInfo.travel')`, etc.
- Line 100: `"Interests"` → `t('personalInfo.interests')`
- Line 114: `"Save Changes"` → `t('personalInfo.saveChanges')`

### SignInScreen.tsx
- Line 31: `"Welcome Back"` → `t('signIn.welcomeBack')`
- Line 32: `"Continue your journey to fluency."` → `t('signIn.subtitle')`
- Line 40: `"Email Address"` → `t('signIn.email')`
- Line 54: `"Password"` → `t('signIn.password')`
- Line 55: `"Forgot Password?"` → `t('signIn.forgotPassword')`
- Line 75: `"Sign In"` → `t('signIn.signIn')`
- Line 84: `"or continue with"` → `t('signIn.orContinueWith')`
- Line 96: `"Continue with Google"` → `t('signIn.continueWithGoogle')`
- Line 100: `"Don't have an account?"` → `t('signIn.noAccount')`
- Line 105: `"Create one now"` → `t('signIn.createAccount')`

### SignUpScreen.tsx
- Line 37-38: `"Join the Academy"` → Use `t('signUp.joinAcademy')` with HTML
- Line 40: `"Enter your details..."` → `t('signUp.subtitle')`
- Line 47: `"Full Name"` → `t('signUp.fullName')`
- Line 53: `"Master Confucius"` → `t('signUp.placeholderName')`
- Line 60: `"Email Address"` → `t('signUp.email')`
- Line 73: `"Password"` → `t('signUp.password')`
- Line 94: `"Create Account"` → `t('signUp.createAccount')`
- Line 103: `"Mastery awaits"` → `t('signUp.masteryAwaits')`
- Line 107: `"Already have an account?"` → `t('signUp.hasAccount')`
- Line 112: `"Sign In"` → `t('signUp.signIn')`

### ForgotPasswordScreen.tsx
- Line 29-30: `"Forgot Password?"` → Use `t('forgotPassword.title')` with HTML
- Line 32-33: Subtitle → `t('forgotPassword.subtitle')`
- Line 40: `"Email address"` → `t('forgotPassword.email')`
- Line 52: `"Send Reset Link"` → `t('forgotPassword.sendLink')`
- Line 59-60: `"Remember your password?"` → `t('forgotPassword.rememberPassword')`
- Line 65: `"Log in"` → `t('forgotPassword.logIn')`

### ConversationScreen.tsx
- Line 132: Error message → `t('conversation.speechNotSupported')`
- Line 165: Mode status strings → `t('conversation.normalModeActive')`, etc.
- Line 198: `'Hide Pinyin'` / `'Aa Pinyin'` → `t('conversation.hidePinyin')` / `t('conversation.showPinyin')`
- Line 206: `'Hide Translate'` / `'A文 Translate'` → `t('conversation.hideTranslate')` / `t('conversation.showTranslate')`
- Line 218: `'Replaying...'` / `'🔁 Repeat'` → `t('conversation.replaying')` / `t('conversation.repeat')`
- Line 270: `"Type or speak…"` → `t('conversation.placeholder')`

### VoiceConversationScreen.tsx
- Line 182: `'Listening...'` → `t('voiceConversation.listening')`
- Line 185: Alert message → `t('voiceConversation.micRequired')`
- Line 239: `'Could not hear anything clearly.'` → `t('voiceConversation.couldNotHear')`
- Line 244: Error message → `t('voiceConversation.connectionError')` + `t('voiceConversation.serverFailed')`
- Line 269: Comment (Spanish already)
- Line 283: `"← Back"` → `t('voiceConversation.back')`
- Line 286: `'Focus'` / `'Roleplay'` → `t('voiceConversation.focus')` / `t('voiceConversation.roleplay')`
- Line 325: interimText handling
- Line 330: `"Transcribing audio..."` → `t('voiceConversation.transcribing')`
- Line 335: `"Processing..."` → `t('voiceConversation.processing')`
- Line 351: `"Repetir frase"` → `t('voiceConversation.repeatPhrase')`
- Line 363: `"Transcript History"` → `t('voiceConversation.transcriptHistory')`

### ConversationContainer.tsx
- Line 120: `'Tars error:'` → `t('conversationContainer.error')`
- Line 259: `'Socket not open, reconnecting...'` → `t('conversationContainer.socketReconnecting')`
- Line 315: `'Reconnect failed'` → `t('conversationContainer.reconnectFailed')`

### apiConfig.ts
- Line 24: Console log message (already Spanish, can keep or standardize)

## Notes
- Some strings in SignUpScreen and ForgotPasswordScreen have HTML `<span>` tags inside - these need special handling with `Trans` component from react-i18next or use `dangerouslySetInnerHTML`
- The `ConversationScreen.tsx` line 141 has `recog.lang = 'en-US'` - this should potentially change to `'es-ES'` for Spanish speech recognition, but since the app teaches Chinese, it might need to stay as is or be configurable
- Backend API responses (greeting messages, etc.) are not covered by frontend i18n - those would need separate handling on the backend
