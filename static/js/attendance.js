/** 学生签到页：保存匿名设备 ID，获取 GPS，并把数据交给后端校验。 */
(() => {
  const id = localStorage.device_id || crypto.randomUUID();
  localStorage.device_id = id;
  document.querySelector("#id_device_id").value = id;
  const status = document.querySelector("#location-status");
  navigator.geolocation.getCurrentPosition(
    (p) => {
      document.querySelector("#id_lat").value = p.coords.latitude;
      document.querySelector("#id_lng").value = p.coords.longitude;
      status.textContent = `定位成功（精度约 ${Math.round(p.coords.accuracy)} 米）`;
      document.querySelector("#submit").disabled = false;
    },
    () => (status.textContent = "定位失败，请允许位置权限后刷新页面"),
    { enableHighAccuracy: true, timeout: 10000 },
  );
})();
