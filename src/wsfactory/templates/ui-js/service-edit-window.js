/**
 * Created by timic on 5/19/14.
 */


function addApi() {

    var apiGrid = getGrid(),
        store = apiGrid.getStore(),
        storeKeys = [];

    store.each(function(rec){
       storeKeys.push(rec.id);
    });

    Ext.Ajax.request({
        url: "{{ component.select_api_url }}",
        params: {
            exclude: JSON.stringify(storeKeys)
        },
        success: function(res, opt) {
            var result = smart_eval(res.responseText);
            result.on("closed_ok", updateStore);
        },
        failure: uiAjaxFailMessage
    })
}


function deleteApi() {

    var grid = getGrid(),
        store = grid.getStore(),
        selectionContext = grid.getSelectionContext(),
        selectedIds = selectionContext.row_id.split(",");

    Ext.each(selectedIds, function(item, index, all){
        var rec = store.getById(item);
        store.remove(rec);
    });
}


function updateStore(codes, displayTexts){

    var apiGrid = getGrid(),
        store = apiGrid.getStore(),
        codeList = codes.split(","),
        displayTextList = displayTexts.split(",");

    Ext.each(codeList, function(item, index, all){
        store.add(
            new store.recordType({id: item, code: item, name: displayTextList[index]}, item));
    });

}


function getGrid(){
    return Ext.getCmp("{{ component.api_grid.client_id }}");
}


function onApiEditing(store) {

    var apiJsonField = Ext.getCmp("{{ component.api_json_field.client_id }}"),
        items = [];

    store.each(function(record){
        var obj = record.data;
        items.push(obj.code);
    });

    var result = JSON.stringify(items);

    apiJsonField.setValue(result);

}