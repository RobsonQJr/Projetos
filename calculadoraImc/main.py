peso = float(input("Digite seu peso (em quilogramas):"))
altura = float(input("Digite sua altura(em metros):"))

imc = peso / (altura **2)

if imc <= 18.5:
    print('Você está abaixo do peso normal')
elif imc >= 18.6 and imc <= 24.9:
    print('Você está com o peso normal')
else:
    print('Excesso de peso') 

