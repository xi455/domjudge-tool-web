// 获取id="problemList"底下的所有li元素
const problemList = document.querySelector("#problemList");
const selectedProblem = document.querySelector("#selectedProblem");
const liItems = problemList.querySelectorAll("li");

function problemListInit() {
  const problemListli = problemList.querySelectorAll("li");
  problemListli.forEach((li) => {
    li.style.cursor = "pointer";
    li.addEventListener("click", moveToSelectedProblem);
  });

  const selectedProblemli = selectedProblem.querySelectorAll("li");
  selectedProblemli.forEach((li) => {
    li.style.cursor = "pointer";
    li.addEventListener("click", moveToProblemList);
  });
}

function moveToSelectedProblem(event) {
  const li = event.target;
  // 移除原來的點擊事件監聽器
  li.removeEventListener("click", moveToSelectedProblem);
  // 添加新的點擊事件監聽器
  li.addEventListener("click", moveToProblemList);
  // 將被點擊的li元素從problemList移動到selectedProblem
  selectedProblem.appendChild(li);
}

function moveToProblemList(event) {
  const li = event.target;
  // 移除原來的點擊事件監聽器
  li.removeEventListener("click", moveToProblemList);
  // 添加新的點擊事件監聽器
  li.addEventListener("click", moveToSelectedProblem);
  // 將被點擊的li元素從selectedProblem移動到problemList
  problemList.appendChild(li);
}

function allPlusSelection() {
  const liItems = problemList.querySelectorAll("li");
  liItems.forEach((li) => {
      // { target: li } 實際上是模擬了一個事件物件，它讓 moveToSelectedProblem 函數可以像在事件處理上下文中一樣訪問 event.target。
      moveToSelectedProblem({ target: li });
  });
}

function withdrawalOfAll() {
  const liItems = selectedProblem.querySelectorAll("li");
  liItems.forEach((li) => {
      moveToProblemList({ target: li });
  });
}

function getSelectedProblem(){
  const liItems = selectedProblem.querySelectorAll("li");
  let chooseProblem = [];
  liItems.forEach((li) => {
      chooseProblem.push({
        "name": li.dataset.name,
        "local_id": li.dataset.localpid,
          "id": li.dataset.pid,
      });
  });

  let selectedProblemHidden = document.querySelector("#selectedProblemHidden");
  let contestHidden = document.querySelector("#contestHidden");
  let form = document.querySelector("#formPost");

  selectedProblemHidden.value = JSON.stringify(chooseProblem);
  contestHidden.value = contestDataJson;
  
  console.log(selectedProblemHidden.value);
  console.log(form);
  console.log(contestHidden.value);

  form.submit();
}

problemListInit();