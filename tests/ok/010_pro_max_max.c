double balance;
double rateNum;     
double rateDen;     
double payment;

int month, maxMonths;
char status;

;

balance = 10000;
rateNum = 2;        
rateDen = 100;     
payment = 500;

month = 0;
maxMonths = 36;

while ( (balance > 0) && (month < maxMonths) ) {
   
    balance = balance + (balance * rateNum) / rateDen - payment;
    month = month + 1;
}

if (balance <= 0) {
    status = "PAGADO";
} else {
    status = "ACTIVO";
}
