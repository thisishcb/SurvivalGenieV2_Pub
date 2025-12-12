// plotly figures to svg
function plotlySvgFilter (node) {
    return (node);
}

function saveSvgToFile(svgData, filename) {
    const link = document.createElement('a');
    link.href = svgData;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
}

function getPlotSvg(index) {
    const btn = document.querySelector(`[id*=${index}]`)
    // const btn = dash_clientside.select_element(`[id="${id}"]`)
    const figures = btn.closest(".card").querySelectorAll('.dash-graph');
    if (figures.length > 1) {
        figure = btn.closest(".card").querySelector(".show").querySelector('.dash-graph').querySelector(".main-svg");
    } else {
        figure = btn.closest(".card").querySelector('.dash-graph').querySelector(".main-svg")
    };
    const clone = figure.cloneNode(true);
    clone.removeAttribute("xmlns:xlink");  // optional, if present
    // clone.setAttribute("xmlns", "http://www.w3.org/2000/svg");
    const svgxml_serializer = new XMLSerializer();
    const svgString = svgxml_serializer.serializeToString(clone);
    const blob = new Blob([svgString], { type: "image/svg+xml;charset=utf-8" });
    const res_url = URL.createObjectURL(blob);
    return(res_url);
}

function downloadPlotSVG(index){
    // so plotly.js has an api all the time????
    const btn = document.querySelector(`[id*=${index}]`)
    // const btn = dash_clientside.select_element(`[id="${id}"]`)
    const figures = btn.closest(".card").querySelectorAll('.dash-graph');
    if (figures.length > 1) {
        figure = btn.closest(".card").querySelector(".show").querySelector('.dash-graph')
    } else {
        figure = btn.closest(".card").querySelector('.dash-graph')
    };
    Plotly.downloadImage(
        figure.querySelector('.js-plotly-plot'),
        { format: 'svg', filename: 'plot' }
        );
}
// const buttons = document.querySelectorAll('.download-figure-button');

// https://community.plotly.com/t/download-component-as-image-using-clientside-callback/59503
// Add a click event listener to each button

// f"save-btn-plot-{type}-{ds}"
// window.addEventListener('load', function() {
//     // Your script logic here
//     console.log('Page loaded!');
//     document.querySelectorAll('.download-figure-button').forEach(button => {
//         button.addEventListener('click', function() {
//           // Get the ID of the clicked button
//           domtoimage.toSvg(getPlotSvg(this.id), {filter: plotlySvgFilter})
//           .then(function (dataUrl) {
//               saveSvgToFile(dataUrl, "new_plot.svg")
//           });
//         });
//       });
      
// });
