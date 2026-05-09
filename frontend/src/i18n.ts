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
