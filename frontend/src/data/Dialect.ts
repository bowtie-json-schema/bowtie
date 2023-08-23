export const Dialect: Dialect = {
    dialectToName: {
        "draft2020-12": "Draft 2020-12",
        "draft2019-09": "Draft 2019-09",
        draft7: "Draft 7",
        draft6: "Draft 6",
        draft4: "Draft 4",
        draft3: "Draft 3",
    },
    dialectMapping: {
        "draft2020-12": "https://json-schema.org/draft/2020-12",
        "draft2019-09": "https://json-schema.org/draft/2019-09",
        draft7: "http://json-schema.org/draft-07",
        draft6: "http://json-schema.org/draft-06",
        draft4: "http://json-schema.org/draft-04",
        draft3: "http://json-schema.org/draft-03",
    }
}

export interface Dialect {
    dialectToName: {
        [key: string]: string;
    };
    dialectMapping: {
        [key: string]: string;
    };
}
