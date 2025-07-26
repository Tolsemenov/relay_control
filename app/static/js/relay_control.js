<script>
  const ws = new WebSocket(`ws://${location.host}/ws`);

  ws.onmessage = function (event) {
    const data = JSON.parse(event.data);

    if (data.type === "status_update") {
      const relayKey = data.relay_key;
      const status = data.status;

      const toggleDiv = document.querySelector(`.switch-toggle[data-relay-key="${relayKey}"]`);
      if (toggleDiv) {
        toggleDiv.classList.toggle("on", status);
        toggleDiv.classList.toggle("off", !status);

        const labelText = toggleDiv.querySelector(".label-text");
        if (labelText) {
          labelText.textContent = status ? "ON" : "OFF";
        }
      }
    }
  };

  ws.onopen = () => console.log("✅ WebSocket соединение установлено");
  ws.onerror = () => console.error("❌ WebSocket ошибка");
  ws.onclose = () => console.warn("🔌 WebSocket соединение закрыто");
</script>
