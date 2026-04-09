document.forms[0].addEventListener("click", function (e) {
    // addFieldBtn が押された場合
    if (e.target.classList.contains("addFieldBtn")) {
        e.preventDefault();

        // 既存の入力行を取得
        const firstField = document.querySelector(".inputField");

        // 入力行を複製
        const clone = firstField.cloneNode(true);

        // 複製した行の input の値を空にする
        clone.querySelector('input[name="new_content[]"]').value = "";

        // select を先頭に戻す
        clone.querySelector('select[name="new_work[]"]').selectedIndex = 0;

        // inputFields の中に追加
        document.querySelector(".inputFields").appendChild(clone);
    }

    // deleteFieldBtn が押された場合
    else if (e.target.classList.contains("deleteFieldBtn")) {
        e.preventDefault();

        const deleteFieldBtns = document.querySelectorAll(".deleteFieldBtn");

        // 入力欄が1つしかない場合は削除不可
        if (deleteFieldBtns.length === 1) {
            alert("入力欄は最低1つ必要です");
            return;
        }

        // 該当行を削除
        const field = e.target.closest(".inputField");
        field.remove();
    }
});

// Enterキーで送信されないようにする
document.addEventListener("keypress", function (e) {
    if (e.key === "Enter") {
        e.preventDefault();
    }
});
