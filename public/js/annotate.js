function loadChart() {
    window.open("/chart", "_self");
}
async function sendAnnotation(element, predict = true) {
    const annotationLoader = new Loader(element.parent(), init = true, small = true)
    const chosen_value = element.val();
    const id = element.parent().parent().attr("id");
    await setPaymentAnnotation({ "id": id, "annotation": chosen_value }).then((res) => {
        console.log(res)
        annotationLoader.stopLoader()
    })
    if (predict) {
        await predictPayments()
    }
    reloadCategory(element)
}
async function addAnnotation(element) {
    const id = element.parent().parent().attr("id");
    // const counterparty_name = element.parent().parent().find(".counterparty_name").text();
    await getPaymentAnnotation(id).then((res) => {
        if (res.data) {
            const category = res.data
            element.val(category)
            element.prop('disabled', true);
            element.addClass("annotated")
            element.parent().parent().addClass("annotated")
            element.parent().parent().removeClass("predicted")
            element.removeClass("predicted")
            element.parent().parent().find("td").last().empty()
            element.parent().parent().find("td").last().text("OK")
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
    const predictableIDs = categoriesToPredict.map(function (element) { return $(element).attr("id") }).get();
    batchPredict(predictableIDs).then((res) => {
        categoriesToPredict.each(function(index){
            if(res.data[index]){
                setPrediction($(this), res.data[index])
            }
        })
    })
}
async function annotateWithPrediction() {
    category = $(this).parent().parent().find(".category").first()
    console.log(category);
    await sendAnnotation(category, predict = false);
}