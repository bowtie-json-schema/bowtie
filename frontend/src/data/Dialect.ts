export const Dialect: Dialect = {
  toShortName: {
    "draft2020-12": "Draft 2020-12",
    "draft2019-09": "Draft 2019-09",
    draft7: "Draft 7",
    draft6: "Draft 6",
    draft4: "Draft 4",
    draft3: "Draft 3",
  },
  toURI: {
    "draft2020-12": "https://json-schema.org/draft/2020-12/schema",
    "draft2019-09": "https://json-schema.org/draft/2019-09/schema",
    draft7: "http://json-schema.org/draft-07/schema#",
    draft6: "http://json-schema.org/draft-06/schema#",
    draft4: "http://json-schema.org/draft-04/schema#",
    draft3: "http://json-schema.org/draft-03/schema#",
  },
};

export interface Dialect {
  toShortName: { [key: string]: string };
  toURI: { [key: string]: string };
}
