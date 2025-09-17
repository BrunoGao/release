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

    const routeLocation: RouteLocationRaw = {
      name: key
    };

    if (Object.keys(query || {}).length) {
      routeLocation.query = query;
    }

    if (Object.keys(params || {}).length) {
      routeLocation.params = params;
    }

    return routerPush(routeLocation);
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
      // Import both auth and customer stores dynamically to avoid circular dependencies
      Promise.all([
        import('@/store/modules/auth'),
        import('@/store/modules/customer')
      ]).then(([{ useAuthStore }, { useCustomerStore }]) => {
        const authStore = useAuthStore();
        const customerStore = useCustomerStore();
        
        // 确定要使用的customerId
        let customerId = authStore.userInfo.customerId;
        
        // 如果是admin用户且已选择客户，使用选中的客户ID
        if (authStore.userInfo?.userName === 'admin' && customerStore.currentCustomerId) {
          customerId = customerStore.currentCustomerId;
        }
        
        const bigscreenUrl = import.meta.env.VITE_BIGSCREEN_URL || 'http://localhost:5002';
        const url = `${bigscreenUrl}/main?customerId=${customerId}`;
        console.log('Opening bigscreen URL:', url);
        console.log('Using customerId:', customerId, '(admin selected:', customerStore.currentCustomerId, ')');
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
    return routerPushByKey('root');
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

    console.log('[redirectFromLogin] needRedirect:', needRedirect, 'redirect:', redirect);

    if (needRedirect && redirect) {
      console.log('[redirectFromLogin] Redirecting to:', redirect);
      await routerPush(redirect);
    } else {
      console.log('[redirectFromLogin] Going to home');
      await toHome();
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
