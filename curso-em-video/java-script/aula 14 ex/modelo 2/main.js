function carregar(){

var msg = window.document.getElementById('msg')
var img = window.document.getElementById('imagem')
var data = new Date()
var hora = data.getHours()

msg.innerHTML = `Agora são ${hora} horas.`


if(hora >= 0 && hora < 12){
    //Bom dia
    img.src = '_img/morning.png'
    document.body.style.background = '#E69937'
} else if(hora >= 12 && hora <= 18){
    //Boa tarde
    img.src = '_img/afternoon.png'
    document.body.style.background = '#F1886F'
}else{
    //Boa noite
    img.src = '_img/nigth.png'
    document.body.style.background = '#293135'
}
}