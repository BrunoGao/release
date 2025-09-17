import type { AxiosResponse } from 'axios';
import { BACKEND_ERROR_CODE, REQUEST_LANGUAGE, createFlatRequest, createRequest } from '@sa/axios';
import { useAuthStore } from '@/store/modules/auth';
import { useCustomerStore } from '@/store/modules/customer';
import { $t } from '@/locales';
import { localStg } from '@/utils/storage';
import { getServiceBaseURL } from '@/utils/service';
import { getAuthorization, getLanguage, handleExpiredRequest, showErrorMsg } from './shared';
import type { RequestInstanceState } from './type';

// 不需要自动添加customerId的API白名单
const EXCLUDE_CUSTOMER_ID_URLS = [
  '/auth/', // 认证相关
  '/login', // 登录
  '/refresh', // 刷新token
  '/sys/dict', // 字典数据(全局)
  '/captcha', // 验证码
  '/logout' // 登出
];

// 修复：在生产环境中也应该使用代理前缀（如果配置了VITE_HTTP_PROXY=Y）
const isHttpProxy = import.meta.env.VITE_HTTP_PROXY === 'Y';
const { baseURL, otherBaseURL } = getServiceBaseURL(import.meta.env, isHttpProxy);

export const request = createFlatRequest<App.Service.Response, RequestInstanceState>(
  {
    baseURL
  },
  {
    async onRequest(config) {
      const authStore = useAuthStore();
      const customerStore = useCustomerStore();
      const Authorization = getAuthorization();
      const language = getLanguage();

      // 确定要使用的customerId
      let customerId = authStore.userInfo.customerId;

      // 如果是admin用户且已选择客户，使用选中的客户ID
      if (authStore.userInfo?.userName === 'admin' && customerStore.currentCustomerId) {
        customerId = customerStore.currentCustomerId;
      }

      // 自动添加customerId (排除白名单URL)
      const shouldAddCustomerId = customerId !== undefined && !EXCLUDE_CUSTOMER_ID_URLS.some(excludeUrl => config.url?.includes(excludeUrl));
      // 调试信息
      if (import.meta.env.DEV) {
        console.log('[Request] customerId injection:', {
          url: config.url,
          method: config.method,
          userCustomerId: authStore.userInfo.customerId,
          selectedCustomerId: customerStore.currentCustomerId,
          finalCustomerId: customerId,
          userName: authStore.userInfo?.userName,
          shouldAdd: shouldAddCustomerId
        });
      }

      if (shouldAddCustomerId) {
        if (config.method?.toLowerCase() === 'get') {
          // GET请求：添加到查询参数
          config.params = config.params || {};
          // 只有当参数中没有customerId时才添加（避免覆盖显式传入的值）
          if (config.params.customerId === undefined) {
            config.params.customerId = customerId;
          }
        } else {
          // POST/PUT/DELETE等请求：添加到请求体
          if (config.data === undefined || config.data === null) {
            config.data = {};
          }
          // 处理FormData类型的请求体
          if (config.data instanceof FormData) {
            if (!config.data.has('customerId')) {
              config.data.append('customerId', String(customerId));
            }
          } else if (typeof config.data === 'object') {
            // 只有当请求体中没有customerId时才添加
            if (config.data.customerId === undefined) {
              config.data.customerId = customerId;
            }
          }
        }
      }

      Object.assign(config.headers, { Authorization, [REQUEST_LANGUAGE]: language });

      return config;
    },
    isBackendSuccess(response) {
      // when the backend response code is "0000"(default), it means the request is success
      // to change this logic by yourself, you can modify the `VITE_SERVICE_SUCCESS_CODE` in `.env` file
      const success = String(response.data.code) === import.meta.env.VITE_SERVICE_SUCCESS_CODE;
      console.log('[Request] isBackendSuccess check:', {
        responseCode: response.data.code,
        expectedCode: import.meta.env.VITE_SERVICE_SUCCESS_CODE,
        success
      });
      return success;
    },
    async onBackendFail(response, instance) {
      const authStore = useAuthStore();
      const responseCode = String(response.data.code);
      function handleLogout() {
        authStore.resetStore();
      }

      function logoutAndCleanup() {
        handleLogout();
        window.removeEventListener('beforeunload', handleLogout);
        request.state.errMsgStack = request.state.errMsgStack.filter(msg => msg !== response.data.message);
      }

      // when the backend response code is in `logoutCodes`, it means the user will be logged out and redirected to login page
      const logoutCodes = import.meta.env.VITE_SERVICE_LOGOUT_CODES?.split(',') || [];
      if (logoutCodes.includes(responseCode)) {
        handleLogout();
        return null;
      }

      // when the backend response code is in `modalLogoutCodes`, it means the user will be logged out by displaying a modal
      const modalLogoutCodes = import.meta.env.VITE_SERVICE_MODAL_LOGOUT_CODES?.split(',') || [];
      if (modalLogoutCodes.includes(responseCode) && !request.state.errMsgStack?.includes(response.data.message)) {
        request.state.errMsgStack = [...(request.state.errMsgStack || []), response.data.message];

        // prevent the user from refreshing the page
        window.addEventListener('beforeunload', handleLogout);

        window.$dialog?.error({
          title: $t('common.error'),
          content: response.data.message,
          positiveText: $t('common.confirm'),
          maskClosable: false,
          closeOnEsc: false,
          onPositiveClick() {
            logoutAndCleanup();
          },
          onClose() {
            logoutAndCleanup();
          }
        });

        return null;
      }

      // when the backend response code is in `expiredTokenCodes`, it means the token is expired, and refresh token
      // the api `refreshToken` can not return error code in `expiredTokenCodes`, otherwise it will be a dead loop, should return `logoutCodes` or `modalLogoutCodes`
      const expiredTokenCodes = import.meta.env.VITE_SERVICE_EXPIRED_TOKEN_CODES?.split(',') || [];
      if (expiredTokenCodes.includes(responseCode)) {
        const success = await handleExpiredRequest(request.state);
        if (success) {
          const Authorization = getAuthorization();
          const language = getLanguage();
          Object.assign(response.config.headers, { Authorization, [REQUEST_LANGUAGE]: language });

          return instance.request(response.config) as Promise<AxiosResponse>;
        }
      }

      return null;
    },
    transformBackendResponse(response) {
      return response.data.data;
    },
    onError(error) {
      // when the request is fail, you can show error message

      let message = error.message;
      let backendErrorCode = '';

      // get backend error message and code
      if (error.code === BACKEND_ERROR_CODE) {
        message = error.response?.data?.message || message;
        backendErrorCode = String(error.response?.data?.code) || '';
      }

      // the error message is displayed in the modal
      const modalLogoutCodes = import.meta.env.VITE_SERVICE_MODAL_LOGOUT_CODES?.split(',') || [];
      if (modalLogoutCodes.includes(backendErrorCode)) {
        return;
      }

      // when the token is expired, refresh token and retry request, so no need to show error message
      const expiredTokenCodes = import.meta.env.VITE_SERVICE_EXPIRED_TOKEN_CODES?.split(',') || [];
      if (expiredTokenCodes.includes(backendErrorCode)) {
        return;
      }

      showErrorMsg(request.state, message);
    }
  }
);

export const demoRequest = createRequest<App.Service.DemoResponse>(
  {
    baseURL: otherBaseURL.demo
  },
  {
    async onRequest(config) {
      const { headers } = config;

      // set token
      const token = localStg.get('token');
      const Authorization = token ? `Bearer ${token}` : null;
      Object.assign(headers, { Authorization });

      return config;
    },
    isBackendSuccess(response) {
      // when the backend response code is "200", it means the request is success
      // you can change this logic by yourself
      return response.data.status === '200';
    },
    async onBackendFail(_response) {
      // when the backend response code is not "200", it means the request is fail
      // for example: the token is expired, refresh token and retry request
    },
    transformBackendResponse(response) {
      return response.data.result;
    },
    onError(error) {
      // when the request is fail, you can show error message

      let message = error.message;

      // show backend error message
      if (error.code === BACKEND_ERROR_CODE) {
        message = error.response?.data?.message || message;
      }

      window.$message?.error(message);
    }
  }
);
