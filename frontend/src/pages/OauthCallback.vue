<!-- src/pages/OauthCallback.vue -->
<script setup>
import { onMounted } from "vue";
import { useRouter } from "vue-router";

const ACCESS_KEY = "access_token";
const REFRESH_KEY = "refresh_token";
const router = useRouter();

onMounted(() => {
  // URL 예: /oauth/callback#provider=google&access=...&refresh=...
  const hash = window.location.hash?.replace(/^#/, "") || "";
  const params = new URLSearchParams(hash);
  const access = params.get("access");
  const refresh = params.get("refresh");

  if (access) localStorage.setItem(ACCESS_KEY, access);
  if (refresh) localStorage.setItem(REFRESH_KEY, refresh);

  // 파싱 후 해시 제거(민감정보 흔적 제거)
  history.replaceState(null, "", window.location.pathname);

  // 적절한 다음 화면으로 이동
  router.replace("/");
});
</script>

<template>
  <div class="p-6 text-sm text-gray-600">로그인 처리 중입니다…</div>
</template>
