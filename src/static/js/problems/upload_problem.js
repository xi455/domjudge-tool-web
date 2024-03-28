function removeRow(button) {
    // 獲取按鈕的父元素的父元素，也就是 tr 元素
    let row = button.parentElement.parentElement;
    // 從 tr 元素的父元素（也就是 table 或者 tbody 元素）中移除 tr 元素
    row.parentElement.removeChild(row);
}

function getServerName(){
    inputSubmit.disabled = true
    contestsSelect.innerHTML = ""

    const serverNameDict = {
        "name": domserverSelect.value
    }

    return serverNameDict;
}

function getProblemID() {
    let problemHiddenID = document.querySelectorAll('input[name="problemHiddenID"]');
    let values = Array.from(problemHiddenID).map(function(inp) {
        return inp.value;
    });

    return values;
}

function updateContestSelect(contestsData){
    for(key in contestsData){
        contestsSelect.innerHTML += `<option value="${contestsData[key]}">${key}</option>;`
    }

    inputSubmit.disabled = false
}

function updateProblemTable(uploadProblemInfo){
    let html = '';
    let index = 0;
    for (let key in uploadProblemInfo) {
        const items = uploadProblemInfo[key];
        html += `
            <tr class="problemTableTr">
            <input type="hidden" name="problemHiddenID" value="${items.problem_id}">
            <th scope="row">${index + 1}</th>
            <td>${key}</td>
            <td>${items.web_problem_state == '已上傳' ? '已上傳' : '未上傳'}</td>
            <td>${items.web_problem_state == '已上傳' ? '<button type="button" name="errorButton" class="btn btn-danger btn-sm" onclick="removeRow(this)">移除</button>' : ''}</td>
            </tr>
        `;
        index++;
    }
    // 假設你的表格的 id 是 'myTable'
    document.querySelector('#problemTable').innerHTML = html;
}

function alertError(error, errorMessage){
    if(error){
        console.error('Error:', error);
    }

    contentHeader.innerHTML += `
    <div class="alert alert-danger" role="alert">
    ${errorMessage}
    </div>
    `
}

function formValidation(){
    const problemTableTr = document.querySelectorAll('.problemTableTr');
    if (problemTableTr.length < 1) {
        alertError(null, '請先選擇題目！！');
        return false;
    }

    const errorButton = document.querySelectorAll('[name="errorButton"]');
    if (errorButton.length > 0) {
        alertError(null, '請先移除未上傳的題目！！');
        return false;
    }
}

document.querySelector('#form').addEventListener('submit', function(event) {
    event.preventDefault();

    if(formValidation() === false){
        return;
    }

    const problemIDArray = getProblemID();
    const problemIDJson = JSON.stringify(problemIDArray);
    document.querySelector('[name="problemIdHidden"]').value = problemIDJson;

    this.submit();
});

domserverSelect.addEventListener('change', function() {
    const serverNameDict = getServerName();
    const problemIDArray = getProblemID();

    fetch("/contests-list/", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrfToken,
        },
        body: JSON.stringify({
            "serverNameDict": serverNameDict,
            "problemIDArray": problemIDArray,
        })
    })
    .then(response => response.json())
    .then(data => {
        const contestsData = data.contests_data;
        const uploadProblemInfo = data.upload_problem_info;
    
        updateContestSelect(contestsData);
        updateProblemTable(uploadProblemInfo);
    })

    .catch(error => {
        alertError(error, '考試選擇區域讀取錯誤！！');            
    });
});