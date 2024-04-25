function loadChart() {
    window.open("/chart", "_self");
}
async function sendAnnotation(element, predict = true) {
    const annotationLoader = new Loader(element.parent(), init = true, small = true)
    const chosen_value = element.val();
    const id = element.parent().parent().attr("id");
    await setPaymentAnnotation({ "id": id, "annotation": chosen_value }).then((res) => {
        annotationLoader.stopLoader()
    })
    setAnnotation(element, chosen_value);
    if (predict) {
        await predictPayments()
    }
}
async function setAnnotation(element, category){
    element.val(category)
    element.addClass("annotated")
    element.parent().parent().addClass("annotated")
    element.parent().parent().removeClass("predicted")
    element.removeClass("predicted")
    element.parent().parent().find("td").last().empty()
    element.parent().parent().find("td").last().text("OK")
}
async function addAnnotation(element) {
    const id = element.parent().parent().attr("id");
    // const counterparty_name = element.parent().parent().find(".counterparty_name").text();
    await getPaymentAnnotation(id).then((res) => {
        if (res.data) {
            const category = res.data
            setAnnotation(element, category)
        }
        else {
            if (!$(this).hasClass("predicted")) {
                element.val(null)
            }
        }
    })
}
function setPrediction(element, category) {
    element.val(category)
    element.addClass("predicted")
    element.parent().parent().addClass("predicted")
    acceptButton = $("<button>");
    acceptButton.text("OK")
    acceptButton.on("click", annotateWithPrediction)
    element.parent().parent().find("td").last().empty()
    element.parent().parent().find("td").last().append(acceptButton)
}
async function addPrediction(element) {
    const id = element.parent().parent().attr("id");
    await getPaymentPrediction(id).then((res) => {
        if (res.data) {
            const category = res.data
            setPrediction(element, category)
        }
    })
}
async function reloadCategory(category) {
    const categoryLoader = new Loader(category.parent(), init = true, small = true)
    if (!category.hasClass("annotated")) {
        await addAnnotation(category)
        if (!category.hasClass("annotated")) {
            await addPrediction(category)
        }
    }
    categoryLoader.stopLoader()
}
async function predictOrAnnotatePayments() {
    $(".category").each(async function (index, element) {
        reloadCategory($(this))
    })
}
async function predictPayments() {
    const categoriesToPredict = $(".category").not(".annotated");
    console.log(categoriesToPredict)
    const predictableIDs = categoriesToPredict.map(function (element) { return $(this).parent().parent().attr("id") }).get();
    console.log(predictableIDs)
    var predicted = 0
    batchPredict(predictableIDs).then((res) => {
        console.log(res)
        categoriesToPredict.each(function(index){
            const prediction_index = Number(index) + Number(predicted)
            if(res.data[prediction_index]){
                setPrediction($(this), res.data[prediction_index])
                predicted += 1
            }
        })
    })
}
async function annotateWithPrediction() {
    category = $(this).parent().parent().find(".category").first()
    console.log(category);
    await sendAnnotation(category, predict = false);
}