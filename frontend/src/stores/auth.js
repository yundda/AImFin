import { defineStore } from 'pinia';
import { ref } from 'vue';
import authApi from '@/services/auth.api';

export const useAuthStore = defineStore('auth', () => {
    const user = ref(null);
    const isAuthenticated = ref(false);

    // 현재 사용자 프로필 가져오기
    const fetchUser = async () => {
        try {
            const response = await authApi.get('/users/profile');
            user.value = response.data;
            isAuthenticated.value = true;
            return response.data;
        } catch (error) {
            console.error('Failed to fetch user:', error);
            user.value = null;
            isAuthenticated.value = false;
            throw error;
        }
    };

    // 로그인 (일반)
    const login = async (id, password) => {
        try {
            await authApi.post('/users/auth/login', {
                email: id, // Backend expects 'email' key? Let's assume frontend passes email as ID
                password: password
            });
            // 쿠키가 세팅되었으므로 프로필을 조회하면 됨
            await fetchUser();
        } catch (error) {
            console.error('Login failed:', error);
            throw error;
        }
    };

    // 로그아웃
    const logout = async () => {
        try {
            await authApi.post('/users/auth/logout');
        } catch (error) {
            console.warn('Logout API error:', error);
        } finally {
            user.value = null;
            isAuthenticated.value = false;
        }
    };

    return {
        user,
        isAuthenticated,
        fetchUser,
        login,
        logout
    };
});
