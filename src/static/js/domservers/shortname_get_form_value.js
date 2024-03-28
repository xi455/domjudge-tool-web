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

    let shortNameHidden = document.querySelector("#shortNameHidden");
    shortNameHidden.value = JSON.stringify(inputValues);

    let form = document.querySelector("form[method='post']");

    form.submit();
}