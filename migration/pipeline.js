import "dotenv/config";

export const pipeline = {
  newscode2id: [
    {
      // parse NEWSCODE into parts
      $set: {
        _p: {
          ye: {
            $toInt: {
              $substrCP: ["$NEWSCODE", 0, 4],
            },
          },
          mo: {
            $toInt: {
              $substrCP: ["$NEWSCODE", 4, 2],
            },
          },
          da: {
            $toInt: {
              $substrCP: ["$NEWSCODE", 6, 2],
            },
          },
          ho: {
            $toInt: {
              $substrCP: ["$NEWSCODE", 8, 2],
            },
          },
          mi: {
            $toInt: {
              $substrCP: ["$NEWSCODE", 10, 2],
            },
          },
          se: {
            $toInt: {
              $substrCP: ["$NEWSCODE", 12, 2],
            },
          },
          ms: {
            $toInt: {
              $substrCP: ["$NEWSCODE", 14, 2],
            },
          },
        },
      },
    },
    {
      // build date from parsed parts
      $set: {
        _date: {
          $dateFromParts: {
            year: "$_p.ye",
            month: "$_p.mo",
            day: "$_p.da",
            hour: "$_p.ho",
            minute: "$_p.mi",
            second: "$_p.se",
            millisecond: "$_p.ms",
            timezone: "Asia/Seoul",
          },
        },
      },
    },
    {
      // convert date to seconds since epoch
      $set: {
        ts2secs: {
          $floor: {
            $divide: [
              {
                $toLong: "$_date",
              },
              1000,
            ],
          },
        },
      },
    },
    {
      // convert seconds to hex string
      $set: {
        _tsHex: {
          $toLower: {
            $convert: {
              input: "$ts2secs",
              to: "string",
              base: 16,
            },
          },
        },
      },
    },
    {
      // build new _id from tsHex and last 16 chars of original _id
      $set: {
        _newsId: {
          $toObjectId: {
            $concat: [
              "$_tsHex",
              {
                $substrCP: [
                  {
                    $toString: "$_id",
                  },
                  8,
                  16,
                ],
              },
            ],
          },
        },
      },
    },
  ],

  transform_tmp: [
    {
      $project: {
        _id: "$_newsId",
        dgubun: "$DGUBUN",
        title: "$TITLE",
        seqno: "$SEQNO",
        newscode_ts: { $toLong: "$_date" },
        kind: ["$KIND", "$KIND2"],
        shcodeTop: "$SHCODE",
      },
    },
  ],

  join_news_jmcode: [
    {
      $lookup: {
        from: process.env.CO_JMCODE,
        let: {
          seq: "$seqno",
        },
        pipeline: [
          {
            $match: {
              $expr: {
                $eq: ["$SEQNO", "$$seq"],
              },
            },
          },
          {
            $project: {
              shcode: "$SHCODE",
              expcode: "$EXPCODE",
              _id: 0,
            },
          },
        ],
        as: "shcode",
      },
    },
    {
      // project the joined news_jmcode
      $set: {
        seqno: "$$REMOVE",
      },
    },
    {
      // merge the joined news_jmcode into a new collection
      $merge: {
        into: process.env.CO_TO,
        on: "_id",
        whenMatched: "keepExisting",
        whenNotMatched: "insert",
      },
    },
  ],

  docs_per_batch: [
    null, // match: _id > lastId(must be updated in the loop)
    {
      $sort: {
        _id: 1,
      },
    },
    {
      $limit: process.env.BATCH_SIZE
        ? parseInt(process.env.BATCH_SIZE, 10)
        : 100,
    },
  ],

  lastid_per_batch: [
    {
      $group: {
        _id: null,
        lastId: {
          $last: "$_id",
        },
        nDocs: {
          $sum: 1,
        },
      },
    },
    {
      $project: {
        _id: 0,
        lastId: 1,
        nDocs: 1,
      },
    },
  ],

  newsid2contid: [
    {
      $project:
        /**
         * specifications: The fields to
         *   include or exclude.
         */
        {
          _id: 0,
          seqno: 1,
          parent: "$_id",
          oidrand: {
            $add: [
              {
                $convert: {
                  input: {
                    $substrCP: [
                      {
                        $toString: "$_id",
                      },
                      8,
                      10,
                    ],
                  },
                  to: "long",
                  base: 16,
                },
              },
              1,
            ],
          },
        },
    },
    {
      $set:
        /**
         * field: The field name
         * expression: The expression.
         */
        /**
         * field: The field name
         * expression: The expression.
         */
        {
          oidrand: {
            $toLower: {
              $convert: {
                input: "$oidrand",
                to: "string",
                base: 16,
              },
            },
          },
        },
    },
    {
      $set:
        /**
         * field: The field name
         * expression: The expression.
         */
        {
          _id: {
            $toObjectId: {
              $concat: [
                {
                  $substrCP: [
                    {
                      $toString: "$parent",
                    },
                    0,
                    8,
                  ],
                },
                "$oidrand",
                {
                  $substrCP: [
                    {
                      $toString: "$parent",
                    },
                    18,
                    6,
                  ],
                },
              ],
            },
          },
          oidrand: "$$REMOVE",
        },
    },
  ],

  migrate_cont: [
    {
      $lookup:
        /**
         * from: The target collection.
         * localField: The local join field.
         * foreignField: The target join field.
         * as: The name for the results.
         * pipeline: Optional pipeline to run on the foreign collection.
         * let: Optional variables to use in the pipeline field stages.
         */
        {
          from: "news_cont_p",
          let: {
            seq: "$seqno",
          },
          pipeline: [
            {
              $match: {
                $expr: {
                  $eq: ["$SEQNO", "$$seq"],
                },
              },
            },
            {
              $sort: {
                LINENO: 1,
              },
            },
            {
              $group: {
                _id: "$SEQNO",
                contents: {
                  $push: "$CONTENT",
                },
              },
            },
          ],
          as: "contents",
        },
    },
    {
      $set:
        /**
         * field: The field name
         * expression: The expression.
         */
        {
          seqno: "$$REMOVE",
          contents: {
            $arrayElemAt: ["$contents.contents", 0],
          },
        },
    },
    {
      $merge: {
        into: process.env.CO_TO,
        on: "_id",
        whenMatched: "keepExisting",
        whenNotMatched: "insert",
      },
    },
  ],
};
