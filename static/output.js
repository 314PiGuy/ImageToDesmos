const graph = JSON.parse(sessionStorage.getItem('imageToDesmos') || '{}');
const calculator = Desmos.GraphingCalculator(document.querySelector('#calculator'), {
  expressions: true, settingsMenu: true, zoomButtons: true
});

if (graph.expressions) {
  calculator.setExpressions(graph.expressions.map((latex, id) => ({
    id: `curve-${id}`, latex, color: Desmos.Colors.BLUE, lineWidth: 3
  })));
  const margin = Math.max(graph.width, graph.height) * .06;
  calculator.setMathBounds({
    left: -margin, right: graph.width + margin,
    bottom: -margin, top: graph.height + margin
  });
} else {
  calculator.setExpression({ latex: 'y=\\sin(x)', color: Desmos.Colors.BLUE });
}
