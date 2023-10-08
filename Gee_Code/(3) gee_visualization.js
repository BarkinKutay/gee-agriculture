var data = ee.FeatureCollection("placeholder");

//Visualization Parameters
var palette_1 = ["0000FF", "000080", "800080", "AA00FF", "FF00FF", "FF0000", "FF8000", "FFFF80", "808000" ,"005000" ,"00FF00" , "00FFFF" ];
var palette_2 = ["feebe2","fbb4b9", "f768a1", "c51b8a", "7a0177", "0000FF"];

var month_visualization = {
  min: 1,
  max: 12,
  palette: palette_1,
  opacity: 0.55
};

var peak_visualization = {
    min: 1,
    max: 6,
    palette: palette_2,
    opacity: 0.55
  };


var map_1 = data.reduceToImage({
    properties: ["peak_month"],
    reducer: ee.Reducer.first(),
});

var map_2 = data.reduceToImage({
    properties: ["peak_count"],
    reducer: ee.Reducer.first(),
});

var outline = ee.Image().paint(data, 0, 1);

Map.addLayer(map_1, month_visualization, 'Max Month');
Map.addLayer(map_2, peak_visualization, 'Peak Count', false);


Map.addLayer(outline, {"palette": "black"}, "Outline");



//LEGENDS
function getMonthName(monthNumber) {
  var date = new Date();
  date.setMonth(monthNumber - 1);

  return date.toLocaleString('en-US', {
    month: 'long',
  });
}

//Legend for Peak Month
var legend = ui.Panel({
  style: {
    position: 'bottom-left',
    padding: '8px 15px'
  }
});
var legendTitle = ui.Label({
  value: 'Peak Month',
  style: {
    fontWeight: 'bold',
    fontSize: '18px',
    margin: '0 0 4px 0',
    padding: '0'
    }
});
legend.add(legendTitle);
var makeRow = function(color, name) {
      var colorBox = ui.Label({
        style: {
          backgroundColor: '#' + color,
          padding: '8px',
          margin: '0 0 4px 0'
        }
      });
      var description = ui.Label({
        value: name,
        style: {margin: '0 0 4px 6px'}
      });
      return ui.Panel({
        widgets: [colorBox, description],
        layout: ui.Panel.Layout.Flow('horizontal')
      });
};

for (var i = 0; i < 12; i++) {
  legend.add(makeRow(palette_1[i], getMonthName(i+1)));
  }  
Map.add(legend);

//Legend for Peak Count
var legend2 = ui.Panel({
    style: {
      position: 'bottom-left',
      padding: '8px 15px'
    }
  });
  var legendTitle = ui.Label({
    value: 'Peak Count',
    style: {
      fontWeight: 'bold',
      fontSize: '18px',
      margin: '0 0 4px 0',
      padding: '0'
      }
  });
  legend2.add(legendTitle);
  var makeRow = function(color, name) {
        var colorBox = ui.Label({
          style: {
            backgroundColor: '#' + color,
            padding: '8px',
            margin: '0 0 4px 0'
          }
        });
        var description = ui.Label({
          value: name,
          style: {margin: '0 0 4px 6px'}
        });
        return ui.Panel({
          widgets: [colorBox, description],
          layout: ui.Panel.Layout.Flow('horizontal')
        });
  };
  
  for (var i = 0; i < 6; i++) {
    legend2.add(makeRow(palette_2[i], i+1));
    }  
Map.add(legend2);