import { defineStore } from 'pinia'

const STORAGE_KEY = 'app_locale'

/** Auth page labels (Login, Register, Forgot password) – ဖုန်းနံပါတ်သက်သက် */
export const authLabels = {
  en: {
    signIn: 'Sign in',
    signInSub: 'Enter your phone number and password.',
    emailOrPhone: 'Phone number',
    phoneNumber: 'Phone number',
    ownerName: 'Owner name',
    forgotPassword: 'Forgot password?',
    signingIn: 'Signing in...',
    signInLink: 'Already have an account? Sign in',
    createAccount: 'Create account',
    createAccountSub: 'Register with your phone number.',
    registerTitle: 'Create account',
    registerSub: 'Register with your phone number.',
    shopName: 'Shop name',
    password: 'Password',
    confirmPassword: 'Confirm password',
    createAccountBtn: 'Create account',
    creating: 'Creating...',
    alreadyHave: 'Already have an account?',
  },
  mm: {
    signIn: 'အကောင့်ဝင်မည်',
    signInSub: 'ဖုန်းနံပါတ်နဲ့ စကားဝှက် ထည့်ပါ။',
    emailOrPhone: 'ဖုန်းနံပါတ်',
    phoneNumber: 'ဖုန်းနံပါတ်',
    ownerName: 'ပိုင်ရှင်အမည်',
    forgotPassword: 'စကားဝှက် မေ့နေပါသလား?',
    signingIn: 'ဝင်နေပါသည်...',
    signInLink: 'အကောင့်ရှိပြီးသား ဆိုရင် ဝင်မည်',
    createAccount: 'အကောင့်ဖွင့်မည်',
    createAccountSub: 'ဖုန်းနံပါတ်ဖြင့် စာရင်းသွင်းပါ။',
    registerTitle: 'အကောင့်ဖွင့်ရန်',
    registerSub: 'ဖုန်းနံပါတ်ဖြင့် စာရင်းသွင်းပါ။',
    shopName: 'ဆိုင်အမည်',
    password: 'စကားဝှက်',
    confirmPassword: 'စကားဝှက် ထပ်ထည့်ပါ',
    createAccountBtn: 'အကောင့်ဖွင့်မည်',
    creating: 'ဖန်တီးနေပါသည်...',
    alreadyHave: 'အကောင့်ရှိပြီးသား လား?',
  },
}

export const useLocaleStore = defineStore('locale', {
  state: () => ({
    locale: (() => {
      try {
        const v = localStorage.getItem(STORAGE_KEY) || 'mm'
        return v === 'my' ? 'mm' : v
      } catch {
        return 'mm'
      }
    })(),
  }),

  getters: {
    lang: (state) => state.locale,
    isEn: (state) => state.locale === 'en',
    isMm: (state) => state.locale === 'mm',
    isMy: (state) => state.locale === 'mm',
  },

  actions: {
    setLang(val) {
      if (val === 'en' || val === 'mm') {
        this.locale = val
        try {
          localStorage.setItem(STORAGE_KEY, val)
        } catch (_) {}
      }
    },
    setLocale(val) {
      this.setLang(val === 'my' ? 'mm' : val)
    },
  },
})
