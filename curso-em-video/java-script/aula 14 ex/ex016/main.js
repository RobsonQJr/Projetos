function contar() {
    let ini = document.getElementById('txti')
    let passo = document.getElementById('txtp')
    let fim = document.getElementById('txtf')
    let res = document.getElementById('res')

    if (ini.value.length == 0 || fim.value.length == 0 || passo.value.length == 0) {
        res.innerHTML = 'Impossível contar'
        

    } else {
        res.innerHTML = 'Contando <br>'
        let i = Number(ini.value)
        let f = Number(fim.value)
        let p = Number(passo.value)

        if (i < f) {
            //Contagem crescente
            for (let c = i; c <= f; c += p) {
                res.innerHTML += `${c} \u{1F449}`
            }
            //Contagem regressiva
        } else {
            for (let c = i; c >= f; c -= p) {
                res.innerHTML += `${c} \u{1F449}`
            }

        }
        res.innerHTML += `\u{1F3C1}`
    }
}
