/**
 * Created by timic on 5/15/14.
 */

function addProtocolParamItem(clientId){
    var grid = Ext.getCmp(clientId),
        store = grid.getStore();
    store.add([
        new store.recordType({
            key: "sampleParam", "value": "sampleValue", value_type: "unicode"
        })
    ]);
}


function deleteProtocolParamItem(clientId){
    var grid = Ext.getCmp(clientId),
        selection = grid.getSelectionContext(),
        store = grid.getStore(),
        rec = store.getById(selection.key);
    store.remove(rec);
}

function onParamEditing(store, jsonFieldId){
    var fld = Ext.getCmp(jsonFieldId),
        items = [];

    store.each(function(record){
        var obj = record.data;
        delete obj.id;
        items.push(obj);
    });

    var result = JSON.stringify(items);

    fld.setValue(result);
}