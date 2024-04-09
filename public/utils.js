var functions;
var provider;
var saveUser;
var getAuthUrl;
var getPayments;
var getOptions;
var hasSavedAccessToken;
var getPaymentPrediction;
var getPaymentAnnotation;
var setPaymentAnnotation;
var getChart;
var getAccounts;
var getUserModel;
var setUserModel;
var batchPredict;

class Loader {
    constructor(div, init = true, small = false) {
        this.div = div;
        this.small = small;
        this.prepareLoader()
        if (init) {
            this.startLoader()
        }
    }
    prepareLoader() {
        this.loadDiv = this.div.clone()
        this.loadDiv.empty()
        this.loadDiv.hide()
        var img = $('<img>')
        img.attr('src', 'assets/loading.gif')
        img.css("margin", "0 auto")
        img.css("width", "30px")
        img.css("margin-left", "calc(50% - 15px)")
        if(!this.small){
            img.css("width", "min(50px , 100%)")
            img.css("margin-top", "calc(25% - 25px)")    
        }
        this.loadDiv.append(img)
        this.loadDiv.css("padding", "0")
        this.loadDiv.css("height", this.div.outerHeight())
        this.loadDiv.insertAfter(this.div)
        // this.div.parent().append(this.loadDiv)
    }

    startLoader() {
        this.loadDiv.css("height", this.div.outerHeight())
        this.div.hide();
        this.loadDiv.show();
    }
    pauseLoader() {
        this.loadDiv.hide();
        this.div.show();
    }
    stopLoader() {
        this.loadDiv.remove();
        this.div.show()
    }
}
document.addEventListener('DOMContentLoaded', function () {
    provider = new firebase.auth.GoogleAuthProvider();
    functions = firebase.app().functions("europe-west1");
    if (window.location.href.includes("localhost")) {
        functions.useEmulator("0.0.0.0", 5001)
    }
    saveUser = functions.httpsCallable('save_user');
    getAuthUrl = functions.httpsCallable('get_auth_url');
    getPayments = functions.httpsCallable('get_payments');
    getOptions = functions.httpsCallable('get_options');
    hasSavedAccessToken = functions.httpsCallable('has_saved_access_token');
    getPaymentPrediction = functions.httpsCallable('get_payment_prediction');
    getPaymentAnnotation = functions.httpsCallable('get_payment_annotation');
    setPaymentAnnotation = functions.httpsCallable('set_payment_annotation');
    getChart = functions.httpsCallable('get_chart');
    getAccounts = functions.httpsCallable('get_accounts');
    getUserModel = functions.httpsCallable('get_user_model');
    setUserModel = functions.httpsCallable('set_user_model');
    batchPredict = functions.httpsCallable('get_batch_prediction');
});

function logout() {
    firebase.auth().signOut()
}

function firebaseLogin() {
    firebase.auth()
        .signInWithPopup(provider)
        .then((result) => {
            /** @type {firebase.auth.OAuthCredential} */
            var credential = result.credential;

            // This gives you a Google Access Token. You can use it to access the Google API.
            var token = credential.accessToken;
            saveUser({ "google_access_token": token }).then((res) => {
                console.log(res)
            })
            // The signed-in user info.
            var user = result.user;
            // IdP data available in result.additionalUserInfo.profile.
            // ...
        }).catch((error) => {
            // Handle Errors here.
            var errorCode = error.code;
            var errorMessage = error.message;
            // The email of the user's account used.
            var email = error.email;
            // The firebase.auth.AuthCredential type that was used.
            var credential = error.credential;
            // ...
        });
}
function bunqAuth(){
    getAuthUrl().then((res) => { window.open(res.data, "_blank") })
}