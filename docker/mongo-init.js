const app = db.getSiblingDB('perso_raw');
app.createUser({user: 'perso_app', pwd: process.env.MONGO_APP_PASSWORD, roles: [{role: 'readWrite', db: 'perso_raw'}]});
