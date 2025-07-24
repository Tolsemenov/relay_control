document.addEventListener("DOMContentLoaded", function () {
  document.querySelectorAll(".relay-toggle").forEach(button => {
    button.addEventListener("click", async () => {
      const relayKey = button.dataset.relayKey;

      try {
        const response = await fetch(`/toggle_relay/${relayKey}`, {
          method: "POST"
        });

        if (!response.ok) throw new Error("Ошибка переключения");

        const data = await response.json();

        const isOn = data.status === true;

        // Обновим классы
        button.classList.toggle("on", isOn);
        button.classList.toggle("off", !isOn);

        // Обновим текст
        const label = button.querySelector(".label-text");
        if (label) label.textContent = isOn ? "ON" : "OFF";

      } catch (err) {
        console.error("Ошибка:", err);
        alert("Ошибка переключения реле");
      }
    });
  });
});