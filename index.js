const functions = require('firebase-functions');

// The Firebase Admin SDK to access the Firebase Realtime Database.
const admin = require('firebase-admin');
admin.initializeApp();

// // Create and Deploy Your First Cloud Functions
// // https://firebase.google.com/docs/functions/write-firebase-functions
//
// exports.helloWorld = functions.https.onRequest((request, response) => {
//  response.send("Hello from Firebase!");
// });

exports.sendNotification = functions.database.ref('/oneOnOneChats/{chatID}/messages/{messageID}').onWrite((change, context) => {
	console.log("Cloud function for sending notifications", 1);
	const addedMssg = change.after.val();
	
	const receiverID = addedMssg.receiverId;
	console.log("Cloud function for sending notifications", 2);
	console.log("Mssg sent is: ", addedMssg.mssgText);
	
	//Don't know what this does
	//if (snapshot.previous.val()) {
     //   return;
  	//} 
  	
	const payload = {
		notification: {
		  title: `New message by ${addedMssg.receiverName}`,
		  body: `${addedMssg.mssgText}`
		}
	};
  	console.log("Cloud function for sending notifications", 3);
  	return admin
        .database()
        .ref(`users/${receiverID}`)
        .once('value')
        .then(data => {
          console.log('inside', data.val().tokenFCM);
          if (data.val().tokenFCM) {
			console.log("Cloud function for sending notifications", 4);
			return admin.messaging().sendToDevice(data.val().tokenFCM, payload);
          }
          else{
          	console.log("Cloud function for sending notifications", 5);
          	return Error("Profile doesn't exist");
          }
        });
 
});

exports.sendData = functions.database.ref('/oneOnOneChats/{chatID}/messages/{messageID}').onWrite((change, context) => {
	console.log("Cloud function for sending data", 1);
	const addedMssg = change.after.val();
	
	const receiverID = addedMssg.recipient.uid;
	console.log("Cloud function for sending data", 2);
	console.log("Mssg sent is: ", addedMssg.mssgText);
	console.log("The receipient is: ", receiverID);
	
	mssgData = JSON.stringify(addedMssg) 
  	
	const payload = {
		data: {
			title: "new mssg",
			body: mssgData
		}	  
	};
  	console.log("Cloud function for sending data", 3);
  	return admin
        .database()
        .ref(`users/${receiverID}`)
        .once('value')
        .then(data => {
          console.log('inside', data.val().tokenFCM);
          if (data.val().tokenFCM) {
			console.log("Cloud function for sending data: ", data.val().tokenFCM);
			return admin.messaging().sendToDevice(data.val().tokenFCM, payload);
          }
          else{
          	console.log("Cloud function for sending data", 5);
          	return Error("Profile doesn't exist");
          }
        });
 
});
