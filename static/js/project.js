window.addEventListener("DOMContentLoaded", function(){
    const agencySelect = document.getElementById("projectAgencyName");
    const accountSelect = document.getElementById("projectAccountName");

    // 初期状態の担当者optionを保存
    const originalOptions = Array.from(accountSelect.querySelectorAll("option"));

    agencySelect.addEventListener("change", function () {
        const selectedAgencyId = this.value;

        // 担当者selectを初期化
        accountSelect.innerHTML = "";

        // 先頭optionを追加
        const defaultOption = document.createElement("option");
        defaultOption.value = "";
        defaultOption.textContent = "担当者を選択";
        defaultOption.disabled = true;
        defaultOption.selected = true;
        accountSelect.appendChild(defaultOption);

        // 選択された代理店に紐づく担当者だけ追加
        originalOptions.forEach(option => {
            const agencyId = option.dataset.agencyId;

            if (
                agencyId === selectedAgencyId &&
                option.value !== ""
            ) {
                accountSelect.appendChild(option.cloneNode(true));
            }
        });
    });
});
