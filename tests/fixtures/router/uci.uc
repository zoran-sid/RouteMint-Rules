// Test-only cursor: faithfully records section order and option changes as JSON.
import { readfile, writefile } from 'fs';
export function cursor(directory, delta) {
    let data;
    return {
        load: function(app) { data = json(readfile(directory + '/' + app)); return !!data; },
        get: function(app, section, option) {
            if (!section || !data[section]) return null;
            return option == null ? data[section]['.type'] : data[section][option];
        },
        set: function(app, section, option, value) {
            if (value == null) { data[section] = {'.name': section, '.type': option}; return true; }
            if (!data[section]) return false;
            data[section][option] = value;
            return true;
        },
        delete: function(app, section, option) {
            if (!data[section]) return false;
            if (option == null) delete data[section];
            else delete data[section][option];
            return true;
        },
        foreach: function(app, kind, callback) {
            for (let name, section in data)
                if (kind == null || section['.type'] === kind) callback(section);
            return true;
        },
        commit: function(app) { return writefile(directory + '/' + app, sprintf('%.J', data)) > 0; }
    };
}
