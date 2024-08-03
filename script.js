function graph(content){
    content.forEach(function (expr){
        console.log(expr);
        calculator.setExpression({latex: expr, color: '#ff0000' });
    })
}


document.getElementById('file')
            .addEventListener('change', (event) => {
                const file = event.target.files[0];
                const reader = new FileReader();
 
                reader.onload = function () {
                    var content = reader.result;
                    content = content.split('\n');
                    graph(content);
                };
 
                reader.onerror = function () {
                    console.error('Error reading the file');
                };
 
                reader.readAsText(file, 'utf-8');
            });
