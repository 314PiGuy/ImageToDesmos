function graph(content){
    content.forEach(function (expr){
        calculator.setExpression({latex: expr, color: '#ff0000' });
    })
  }
  

  graph(funcs);
  