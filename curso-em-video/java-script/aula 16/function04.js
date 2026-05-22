function fatorial(n){
    let fat = 1

    for(let c = n; c > 1; c-- ){
        fat *= c 
    }
    return fat
}

console.log(fatorial(5))


//5! = 5x4,5x3,5x2.5x1