
const Imap = require('/tmp/node_modules/imap');
const imap = new Imap({
user: 'mie@bon-soleil.com',
password: process.env.MAIL_PASSWORD, // Use environment variable for password
host: 'imap4.hetemail.jp',
port: 993,
tls: true,
tlsOptions: { rejectUnauthorized: false }
});

imap.once('ready', function() {
  console.log('Connected to IMAP server!');
  imap.end(); // Disconnect after successful connection
});

imap.once('error', function(err) {
  console.error('IMAP connection error:', err.message); // Only print error message for security
});

imap.once('end', function() {
  console.log('IMAP connection ended.');
});

imap.connect();
