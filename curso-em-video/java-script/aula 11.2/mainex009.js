function calcular() {
    var input = document.getElementById('pais').value
    var res = document.querySelector('div.res')

    if (input.toLowerCase() == 'brasil') {
        res.innerHTML = "Você é brasileiro"
    }
    else {
        res.innerHTML = "Você é estrangeiro"
    }



}