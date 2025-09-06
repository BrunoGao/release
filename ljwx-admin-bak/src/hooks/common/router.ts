import { useRouter } from 'vue-router';
import type { RouteLocationRaw } from 'vue-router';
import type { RouteKey } from '@elegant-router/types';
import { router as globalRouter } from '@/router';

/**
 * Router push
 *
 * Jump to the specified route, it can replace function router.push
 *
 * @param inSetup Whether is in vue script setup
 */
export function useRouterPush(inSetup = true) {
  const router = inSetup ? useRouter() : globalRouter;
  const route = globalRouter.currentRoute;

  const routerPush = router.push;

  const routerBack = router.back;

  interface RouterPushOptions {
    query?: Record<string, string>;
    params?: Record<string, string>;
  }

  async function routerPushByKey(key: RouteKey, options?: RouterPushOptions) {
    const { query, params } = options || {};

    console.log('[Router] routerPushByKey called with key:', key, 'options:', options);

    const routeLocation: RouteLocationRaw = {
      name: key
    };

    if (Object.keys(query || {}).length) {
      routeLocation.query = query;
    }

    if (Object.keys(params || {}).length) {
      routeLocation.params = params;
    }

    console.log('[Router] Final route location:', routeLocation);
    const availableRoutes = router.getRoutes().map(r => ({ name: r.name, path: r.path }));
    console.log('[Router] Available routes:', availableRoutes);
    
    try {
      const result = await routerPush(routeLocation);
      console.log('[Router] routerPush result:', result);
      return result;
    } catch (error) {
      console.error('[Router] routerPush error:', error);
      throw error;
    }
  }

  function routerPushByKeyWithMetaQuery(key: RouteKey) {
    const allRoutes = router.getRoutes();
    const meta = allRoutes.find(item => item.name === key)?.meta || null;

    // Debug logging
    console.log('routerPushByKeyWithMetaQuery called with key:', key);
    console.log('Found meta:', meta);

    // Handle special routes that should open in new window
    if (key === 'bigscreen') {
      console.log('Intercepting bigscreen navigation');
      // Import auth store dynamically to avoid circular dependencies
      import('@/store/modules/auth').then(({ useAuthStore }) => {
        const authStore = useAuthStore();
        const bigscreenUrl = import.meta.env.VITE_BIGSCREEN_URL || 'http://localhost:5002';
        const url = `${bigscreenUrl}/main?customerId=${authStore.userInfo.customerId}`;
        console.log('Opening bigscreen URL:', url);
        window.open(url, '_blank');
      });
      return Promise.resolve();
    }

    const query: Record<string, string> = {};

    meta?.query?.forEach(item => {
      query[item.key] = item.value;
    });

    return routerPushByKey(key, { query });
  }

  async function toHome() {
    console.log('[Router] toHome called, pushing to root');
    const result = await routerPushByKey('root');
    console.log('[Router] toHome routerPushByKey result:', result);
    return result;
  }

  /**
   * Navigate to login page
   *
   * @param loginModule The login module
   * @param redirectUrl The redirect url, if not specified, it will be the current route fullPath
   */
  async function toLogin(loginModule?: UnionKey.LoginModule, redirectUrl?: string) {
    const module = loginModule || 'pwd-login';

    const options: RouterPushOptions = {
      params: {
        module
      }
    };

    const redirect = redirectUrl || route.value.fullPath;

    options.query = {
      redirect
    };

    return routerPushByKey('login', options);
  }

  /**
   * Toggle login module
   *
   * @param module
   */
  async function toggleLoginModule(module: UnionKey.LoginModule) {
    const query = route.value.query as Record<string, string>;

    return routerPushByKey('login', { query, params: { module } });
  }

  /**
   * Redirect from login
   *
   * @param [needRedirect=true] Whether to redirect after login. Default is `true`
   */
  async function redirectFromLogin(needRedirect = true) {
    const redirect = route.value.query?.redirect as string;

    console.log('[Router] redirectFromLogin called');
    console.log('[Router] needRedirect:', needRedirect);
    console.log('[Router] redirect query:', redirect);
    console.log('[Router] current route:', route.value);

    if (needRedirect && redirect) {
      console.log('[Router] Using redirect URL:', redirect);
      routerPush(redirect);
    } else {
      console.log('[Router] Going to home');
      toHome();
    }
  }

  return {
    routerPush,
    routerBack,
    routerPushByKey,
    routerPushByKeyWithMetaQuery,
    toLogin,
    toggleLoginModule,
    redirectFromLogin
  };
}
