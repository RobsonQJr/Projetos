function calcular() {
    var txtv = window.document.getElementById('txtvel')
    var res = window.document.querySelector('div.res')

    var vel = Number(txtv.value)
    res.innerHTML = `Sua velocidade atual é de<p><strong> ${vel} </strong> km/h</p>`
    if (vel > 60) {
        res.innerHTML += `<p>Você passou do limite de velocidade. Multado!</p>`
    } 
        res.innerHTML += `Ande sempre com o cinto de segurança</p>`
    }