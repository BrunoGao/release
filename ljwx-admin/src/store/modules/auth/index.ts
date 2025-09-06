import { computed, reactive, ref } from 'vue';
import { useRoute } from 'vue-router';
import { defineStore } from 'pinia';
import { useLoading } from '@sa/hooks';
import { SetupStoreId } from '@/enum';
import { useRouterPush } from '@/hooks/common/router';
import { fetchGetUserInfo, fetchLogin } from '@/service/api';
import { localStg } from '@/utils/storage';
import { $t } from '@/locales';
import { useRouteStore } from '../route';
import { useTabStore } from '../tab';
import { useDictStore } from '../dict';
import { clearAuthStorage, getToken } from './shared';

export const useAuthStore = defineStore(SetupStoreId.Auth, () => {
  const route = useRoute();
  const routeStore = useRouteStore();
  const tabStore = useTabStore();
  const dictStore = useDictStore();
  const { toLogin, redirectFromLogin } = useRouterPush(false);
  const { loading: loginLoading, startLoading, endLoading } = useLoading();

  const token = ref(getToken());

  const userInfo: Api.Auth.UserInfo = reactive({
    id: '',
    userName: '',
    nickName: '',
    realName: '',
    roleIds: [],
    permissions: [],
    customerId: 0,
    deviceSn: '',
    orgId: []
  });

  /** is super role in static route */
  const isStaticSuper = computed(() => {
    const { VITE_AUTH_ROUTE_MODE, VITE_STATIC_SUPER_ROLE } = import.meta.env;

    return VITE_AUTH_ROUTE_MODE === 'static' && userInfo.roleIds.includes(VITE_STATIC_SUPER_ROLE);
  });

  /** Is login */
  const isLogin = computed(() => Boolean(token.value));

  /** Reset auth store */
  async function resetStore() {
    const authStore = useAuthStore();

    clearAuthStorage();

    authStore.$reset();

    if (!route.meta.constant) {
      await toLogin();
    }

    tabStore.cacheTabs();
    routeStore.resetStore();
  }

  /**
   * Login
   *
   * @param userName User name
   * @param password Password
   * @param [redirect=true] Whether to redirect after login. Default is `true`
   */
  async function login(userName: string, password: string, redirect = true) {
    startLoading();

    console.log('[Auth] Starting login process for user:', userName);
    const { data: loginToken, error } = await fetchLogin(userName, password);

    if (!error) {
      console.log('[Auth] Login API success, received token:', !!loginToken?.token);
      const pass = await loginByToken(loginToken);

      if (pass) {
        console.log('[Auth] Token login successful, user info:', userInfo);
        await dictStore.init();
        console.log('[Auth] Dictionary initialized');

        // Ensure auth routes are initialized before redirect
        console.log('[Auth] Route init status before check:', routeStore.isInitAuthRoute);
        if (!routeStore.isInitAuthRoute) {
          console.log('[Auth] Initializing auth routes...');
          await routeStore.initAuthRoute();
          console.log('[Auth] Auth routes initialization completed:', routeStore.isInitAuthRoute);
        } else {
          console.log('[Auth] Auth routes already initialized');
        }

        console.log('[Auth] Calling redirectFromLogin with redirect:', redirect);
        await redirectFromLogin(redirect);
        console.log('[Auth] redirectFromLogin completed');

        if (routeStore.isInitAuthRoute) {
          console.log('[Auth] Showing success notification');
          window.$notification?.success({
            title: $t('page.login.common.loginSuccess'),
            content: $t('page.login.common.welcomeBack', { userName: userInfo.userName }),
            duration: 4500
          });
        }
      } else {
        console.log('[Auth] Token login failed');
      }
    } else {
      console.log('[Auth] Login API failed with error:', error);
      resetStore();
    }

    endLoading();
  }

  async function loginByToken(loginToken: Api.Auth.LoginToken) {
    // 1. stored in the localStorage, the later requests need it in headers
    localStg.set('token', loginToken.token);
    // 兼容后端只返回token的情况，使用token作为refreshToken
    localStg.set('refreshToken', loginToken.refreshToken || loginToken.token);

    // 2. get user info
    const pass = await getUserInfo();

    if (pass) {
      token.value = loginToken.token;

      return true;
    }

    return false;
  }

  async function getUserInfo() {
    const { data: info, error } = await fetchGetUserInfo();

    if (!error) {
      // update store
      Object.assign(userInfo, info);

      return true;
    }

    return false;
  }

  async function initUserInfo() {
    const hasToken = getToken();

    if (hasToken) {
      const pass = await getUserInfo();

      if (!pass) {
        resetStore();
      }
    }
  }

  return {
    token,
    userInfo,
    isStaticSuper,
    isLogin,
    loginLoading,
    resetStore,
    login,
    initUserInfo
  };
});
