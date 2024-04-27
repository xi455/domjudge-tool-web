function getFormValue() {
    // 獲取所有選中的复選框的值
    let inputs = document.querySelectorAll('input[class="form-control"]');
    let inputValues = Array.from(inputs).map(function (input) {
        let ids = input.id.split(":");
        return {
            id: ids[0],
            local_id: ids[1],
            name: input.name,
            shortname: input.value ? input.value : input.name,
        };
    });

    // 檢查 shortname 是否重複
    let shortnameCounts = {};
    for (let input of inputValues) {
        if (shortnameCounts[input.shortname]) {
            alert(`簡稱 "${input.shortname}" 重複到！！`);
            return;
        }
        shortnameCounts[input.shortname] = true;
    }

    let shortNameHidden = document.querySelector("#shortNameHidden");
    shortNameHidden.value = JSON.stringify(inputValues);

    let form = document.querySelector("form[method='post']");

    form.submit();
}